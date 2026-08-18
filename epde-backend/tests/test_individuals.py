"""Identity and ancestry, the two things EPDE does not record."""

from __future__ import annotations

import copy

from epdeweb.adapters.individuals import CROSSOVER, MUTATION, IndividualRegistry

from .conftest import make_system


def test_a_copy_carries_the_parent_uid_which_is_what_makes_ancestry_recoverable():
    """The whole mechanism rests on this.

    EPDE breeds by ``deepcopy``, so a record written into the system's
    ``__dict__`` travels into the offspring, and the parent can be read off it
    at the moment the offspring is created. If EPDE ever stopped copying, the
    genealogy would degrade to survival edges -- so the property is asserted
    rather than assumed.
    """
    registry = IndividualRegistry()
    parent = make_system()
    parent_uid = registry.uid_of(parent)

    child = copy.deepcopy(parent)
    assert registry.record_of(child).uid == parent_uid


def test_crossover_then_mutation_stays_one_individual_with_two_operators():
    """An offspring is often crossed and then mutated before anyone sees it.

    Numbering it twice would put a node in the graph that no generation ever
    contained. GOLEM records the same shape as a chain of operators under one
    individual, and so does this.
    """
    registry = IndividualRegistry()
    mother, father = make_system(), make_system()
    parents = [registry.uid_of(mother), registry.uid_of(father)]

    offspring = copy.deepcopy(mother)
    crossed = registry.record_offspring(
        offspring, parents=parents, operator_type=CROSSOVER, label="crossover"
    )
    mutated = registry.record_offspring(
        offspring, parents=[crossed], operator_type=MUTATION, label="mutation"
    )

    assert mutated == crossed
    record = registry.record_of(offspring)
    assert [operator.type_ for operator in record.operators] == [CROSSOVER, MUTATION]
    # Only the first link carries the real parents; the second consumes the
    # first's output, exactly as the graph draws it.
    assert record.operators[0].parent_uids == parents
    assert record.operators[1].parent_uids == []


def test_mutating_a_published_individual_creates_a_new_one():
    registry = IndividualRegistry()
    parent = make_system()
    registry.snapshot([parent], generation=0)
    parent_uid = registry.record_of(parent).uid

    child = copy.deepcopy(parent)
    child_uid = registry.record_offspring(
        child, parents=[parent_uid], operator_type=MUTATION, label="mutation"
    )

    assert child_uid != parent_uid
    assert registry.record_of(child).operators[0].parent_uids == [parent_uid]


def test_a_population_holding_two_copies_of_one_identity_separates_them():
    """EPDE copies candidates for reasons that are not reproduction.

    Both copies then claim the same uid, and a population containing both would
    draw one node where there are two individuals -- with survival edges fanning
    out of a node that is not their ancestor.
    """
    registry = IndividualRegistry()
    original = make_system()
    registry.uid_of(original)
    twin = copy.deepcopy(original)

    records = registry.snapshot([original, twin], generation=0)
    uids = [record.uid for record in records]

    assert len(set(uids)) == 2
    assert records[1].operators[0].type_ == "copy"
    assert records[1].operators[0].parent_uids == [records[0].uid]


def test_the_seed_population_gets_uids_and_no_ancestry():
    registry = IndividualRegistry()
    population = [make_system() for _ in range(3)]

    records = registry.snapshot(population, generation=0)

    assert len({record.uid for record in records}) == 3
    assert all(record.operators == [] for record in records)
    assert all(record.born_generation == 0 for record in records)


def test_publishing_twice_keeps_the_first_generation_it_appeared_in():
    registry = IndividualRegistry()
    system = make_system()
    registry.snapshot([system], generation=0)
    record = registry.snapshot([system], generation=4)[0]

    assert record.born_generation == 0
