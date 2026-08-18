"""Identity and ancestry for EPDE candidate systems.

GOLEM wraps every graph it evolves in an ``Individual``: a uid, the parents it
came from, and the operator that produced it. FEDOT.Web's genealogy is built
entirely out of those three facts. EPDE has none of them -- its optimisers pass
bare ``SoEq`` objects around, and a candidate has no more identity than its
position in a list -- so this module supplies them.

The mechanism rests on one property of how EPDE breeds: an offspring is a
``deepcopy`` of its parent that is then modified. A record written into the
system's ``__dict__`` therefore travels into the copy for free, which is what
makes the parent recoverable at the moment the offspring is created. The
operator hooks in :mod:`epdeweb.adapters.observer` do exactly that -- read the
inherited record, then overwrite it with a fresh one naming the parents it just
read.

Two details this gets right, because both are easy to get wrong and neither
fails loudly:

* An offspring is often crossed *and then* mutated before it is ever seen in a
  population. Numbering it twice would put a phantom individual in the graph
  that no generation ever contained, so a record still awaiting its first
  population accumulates a chain of operators under one uid instead -- the same
  shape GOLEM records in ``operators_from_prev_generation``. "Awaiting" is not
  the same as "not yet published": a candidate the population constructor just
  made is also unpublished, and it is a real individual, not an intermediate.
* EPDE copies systems in places that are not reproduction. Two live objects then
  carry the same uid, and a population containing both would collapse them into
  one node. Duplicates are separated when the population is read, which is the
  only place the ambiguity can actually be observed.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any

#: Where the record is stashed on a candidate system. ``SoEq`` has no
#: ``__slots__`` and its ``__deepcopy__`` copies ``__dict__`` wholesale, so an
#: attribute set here survives the copy that creates an offspring.
RECORD_ATTRIBUTE = "_epdeweb_record"

INITIAL = "initial"
MUTATION = "mutation"
CROSSOVER = "crossover"
COPY = "copy"


@dataclass
class OperatorRecord:
    """One evolutionary operator applied on the way to an individual."""

    uid: str
    type_: str
    label: str
    parent_uids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "type": self.type_,
            "label": self.label,
            "parents": list(self.parent_uids),
        }


@dataclass
class Record:
    """What is known about one candidate system."""

    uid: str
    operators: list[OperatorRecord] = field(default_factory=list)
    #: True once the individual has appeared in a reported population.
    published: bool = False
    #: True between an operator producing this system and the first population
    #: that contains it. Such a system is an *intermediate*: a further operator
    #: extends its chain instead of numbering a new individual, because nothing
    #: ever saw the in-between state. Distinct from ``not published``, which is
    #: also true of a candidate the population constructor has just made and
    #: which is a real individual with no ancestry.
    pending: bool = False
    born_generation: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "operators": [operator.as_dict() for operator in self.operators],
            "published": self.published,
            "pending": self.pending,
            "born_generation": self.born_generation,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Record:
        return cls(
            uid=str(raw.get("uid", "")),
            operators=[
                OperatorRecord(
                    uid=str(entry.get("uid", "")),
                    type_=str(entry.get("type", "")),
                    label=str(entry.get("label", "")),
                    parent_uids=[str(uid) for uid in entry.get("parents") or []],
                )
                for entry in raw.get("operators") or []
            ],
            published=bool(raw.get("published", False)),
            pending=bool(raw.get("pending", False)),
            born_generation=raw.get("born_generation"),
        )


class IndividualRegistry:
    """Assigns and remembers the identity of every candidate system in a run."""

    def __init__(self, prefix: str = "s") -> None:
        self._counter = itertools.count(1)
        self._operator_counter = itertools.count(1)
        self._prefix = prefix

    # ------------------------------------------------------------------ naming

    def _next_uid(self) -> str:
        return f"{self._prefix}{next(self._counter)}"

    def _next_operator_uid(self) -> str:
        return f"op{next(self._operator_counter)}"

    # ------------------------------------------------------------------ reading

    @staticmethod
    def record_of(system: Any) -> Record | None:
        raw = getattr(system, RECORD_ATTRIBUTE, None)
        if isinstance(raw, dict):
            return Record.from_dict(raw)
        return None

    @staticmethod
    def _write(system: Any, record: Record) -> None:
        try:
            setattr(system, RECORD_ATTRIBUTE, record.as_dict())
        except AttributeError:  # pragma: no cover - a system that forbids it
            pass

    def uid_of(self, system: Any) -> str:
        """The uid of a system, assigning one if it has never been seen.

        A system that reaches here without a record was created by the
        population constructor, so it is an individual of the initial
        population and has no ancestry.
        """
        record = self.record_of(system)
        if record is not None and record.uid:
            return record.uid
        record = Record(uid=self._next_uid())
        self._write(system, record)
        return record.uid

    # ------------------------------------------------------------------ writing

    def record_offspring(
        self,
        system: Any,
        *,
        parents: list[str],
        operator_type: str,
        label: str | None = None,
    ) -> str:
        """Note that ``system`` was just produced by an operator.

        Returns the uid the offspring ends up with -- a new one when it descends
        from a published individual, or the existing one when this is a second
        operator applied to an offspring that has not been reported yet.
        """
        operator = OperatorRecord(
            uid=self._next_operator_uid(),
            type_=operator_type,
            label=label or operator_type,
            parent_uids=[uid for uid in parents if uid],
        )

        existing = self.record_of(system)
        if existing is not None and existing.uid and existing.pending and not existing.published:
            # Still an intermediate: extend its chain. The parents are already
            # recorded on the first operator of the chain, so this link carries
            # none -- it consumes the previous operator's output.
            operator.parent_uids = []
            existing.operators.append(operator)
            self._write(system, existing)
            return existing.uid

        record = Record(uid=self._next_uid(), operators=[operator], pending=True)
        self._write(system, record)
        return record.uid

    def publish(self, system: Any, generation: int) -> Record:
        """Mark a system as having appeared in a reported population."""
        record = self.record_of(system)
        if record is None or not record.uid:
            record = Record(uid=self._next_uid())
        if not record.published:
            record.published = True
            record.pending = False
            record.born_generation = generation
        self._write(system, record)
        return record

    def fork_duplicate(self, system: Any, origin_uid: str, generation: int) -> Record:
        """Give a system its own uid when another object already claims one.

        EPDE copies candidate systems in places that are not reproduction --
        archiving, sorting, elitism -- and the copy inherits the record. Left
        alone, a population holding both would draw one node where there are
        two individuals, and the survival edges would fan out from a node that
        is not their real ancestor.
        """
        record = Record(
            uid=self._next_uid(),
            operators=[
                OperatorRecord(
                    uid=self._next_operator_uid(),
                    type_=COPY,
                    label="copy",
                    parent_uids=[origin_uid],
                )
            ],
            published=True,
            born_generation=generation,
        )
        self._write(system, record)
        return record

    # ---------------------------------------------------------------- snapshots

    def snapshot(self, population: list[Any], generation: int) -> list[Record]:
        """Publish a whole population, separating any duplicated identities."""
        seen: set[str] = set()
        records: list[Record] = []
        for system in population:
            record = self.publish(system, generation)
            if record.uid in seen:
                record = self.fork_duplicate(system, record.uid, generation)
            seen.add(record.uid)
            records.append(record)
        return records


#: The run worker installs one registry for the whole process; the operator
#: hooks are patched onto EPDE classes and have no other way to reach it.
_current: IndividualRegistry | None = None


def install_registry(registry: IndividualRegistry | None) -> IndividualRegistry | None:
    global _current
    previous, _current = _current, registry
    return previous


def current_registry() -> IndividualRegistry | None:
    return _current
