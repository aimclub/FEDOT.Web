"""A candidate system of equations, rendered for the browser.

This is the EPDE counterpart of ``fedotweb.pipelines.convert``: it turns the
framework's own object into the structure the canvas and the inspector draw. A
FEDOT pipeline is a graph of operations; an EPDE candidate is a *system of
equations*, and the natural graph is its syntax tree --

    system -> equation (one per described variable)
           -> term     (one per summand, carrying its fitted coefficient)
           -> factor   (the tokens multiplied together inside a term)

so a node in the genealogy can be opened and read the same way a pipeline node
can. The text and LaTeX forms are built here too, because the equation itself is
what a user actually wants to see; the tree explains where it came from.

Everything is duck-typed on purpose. Nothing in this module imports EPDE, which
keeps it testable with stand-ins and keeps the API layer -- which renders stored
payloads -- free of the framework.

Reading an EPDE candidate is defensive throughout. A system is a live object in
the middle of an evolutionary run: its right-hand side may not have been chosen
yet, its weights may not have been fitted, and asking for ``text_form`` before
either raises. Nothing here is allowed to fail a whole generation report, so
every read that can raise is guarded and the corresponding field simply comes
back empty.
"""

from __future__ import annotations

import math
import re
from typing import Any

#: EPDE names the derivative axes positionally and zero-based: whatever the
#: dataset calls its axes, the first is ``x0`` and the second ``x1``
#: (``epde.supplementary.define_derivatives``). So ``d^2u/dx1^2`` on a field
#: laid out (t, x) is the second *spatial* derivative -- correct, and both
#: unreadable and easy to misread as a time derivative. The whole point of
#: renaming is that a wave equation should come back as
#: ``d^2u/dt^2 = d^2u/dx^2`` rather than as ``d^2u/dx0^2 = d^2u/dx1^2``, and
#: getting the base wrong would swap the two while still looking plausible.
_AXIS_IN_LABEL = re.compile(r"x(\d+)")
_AXIS_IN_LATEX = re.compile(r"x_\{?(\d+)\}?")


def _axis_mapping(axis_names: list[str]) -> dict[str, str]:
    return {str(index): name for index, name in enumerate(axis_names)}


def axis_renamer(axis_names: list[str] | None):
    """Rewrite EPDE's positional axis names to the dataset's own.

    Applied only where a name is unambiguously an axis reference -- inside a
    derivative label and in the ``dim`` argument of a coordinate-dependent
    token -- so a variable that happens to be called ``x1`` is left alone.
    """
    if not axis_names:
        return lambda label: label
    mapping = _axis_mapping(axis_names)

    def rename(label: str) -> str:
        return _AXIS_IN_LABEL.sub(lambda match: mapping.get(match.group(1), match.group(0)), label)

    return rename


def latex_axis_renamer(axis_names: list[str] | None):
    """The same substitution inside the LaTeX EPDE builds, where axes are ``x_0``."""
    if not axis_names:
        return lambda text: text
    mapping = _axis_mapping(axis_names)

    def rename(text: str) -> str:
        return _AXIS_IN_LATEX.sub(
            lambda match: mapping.get(match.group(1), match.group(0)), text
        )

    return rename

#: Coefficients below this are reported as inactive terms. EPDE fits the
#: coefficients with LASSO, which drives dropped terms to exactly zero, but the
#: final ordinary-least-squares refit on the surviving terms can leave a
#: denormal behind; treating those as active would show equations padded with
#: terms that contribute nothing.
ZERO_COEFFICIENT = 1e-12


# --------------------------------------------------------------------- factors


def factor_parameters(factor: Any) -> dict[str, float]:
    """The parameters of one token, keyed by name rather than by position.

    EPDE stores them as a numpy array plus a separate description mapping the
    array index to a name (``power``, ``freq``, ``dim``), which is convenient
    for the evolutionary operators and useless for display.
    """
    parameters: dict[str, float] = {}
    description = getattr(factor, "params_description", None) or {}
    values = getattr(factor, "params", None)
    if values is None:
        return parameters
    for index, info in description.items():
        try:
            name = str(info["name"])
            parameters[name] = float(values[index])
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return parameters


def compact_factor(factor: Any, axis_names: list[str] | None = None) -> str:
    """A short readable form of a token: ``du/dt``, ``u^2``, ``sin(1.62 x)``.

    EPDE's own ``Factor.name`` spells every parameter out
    (``du/dx1{power: 1.0}``), which is unreadable once a term has three of them
    and is what the genealogy cards would otherwise be filled with.
    """
    label = str(getattr(factor, "label", "") or "?")
    if "/" in label:
        # A derivative label such as ``d^2u/dx1^2`` is the one place a
        # positional axis name appears in the token itself.
        label = axis_renamer(axis_names)(label)

    parameters = factor_parameters(factor)
    power = parameters.pop("power", 1.0)

    if "freq" in parameters:
        argument = f"{parameters.pop('freq'):.3g}"
        dimension = parameters.pop("dim", None)
        if dimension is not None:
            argument += f" {_axis_label(int(dimension), axis_names)}"
        label = f"{label}({argument})"
    if parameters:
        rest = ", ".join(f"{name}={value:.3g}" for name, value in sorted(parameters.items()))
        label = f"{label}[{rest}]"

    if abs(power - 1.0) > 1e-9:
        power_text = f"{int(power)}" if float(power).is_integer() else f"{power:.3g}"
        label = f"{label}^{power_text}"
    return label


def _display_label(factor: Any, axis_names: list[str] | None) -> str:
    label = str(getattr(factor, "label", "") or "?")
    return axis_renamer(axis_names)(label) if "/" in label else label


def _axis_label(index: int, axis_names: list[str] | None) -> str:
    """Name of one axis. ``dim`` is zero-based, unlike a derivative label."""
    if axis_names and 0 <= index < len(axis_names):
        return axis_names[index]
    return f"x{index}"


def factor_latex(factor: Any, axis_names: list[str] | None = None) -> str:
    """LaTeX for one token, preferring the form EPDE builds for it."""
    try:
        latex = getattr(factor, "latex_name", None)
        if latex:
            return latex_axis_renamer(axis_names)(str(latex))
    except Exception:  # noqa: BLE001 - a token without a LaTeX constructor
        pass
    return _escape_latex(compact_factor(factor, axis_names))


# ----------------------------------------------------------------------- terms


def compact_term(term: Any, axis_names: list[str] | None = None) -> str:
    """A term as the product of its tokens, without coefficients."""
    factors = list(getattr(term, "structure", None) or [])
    if not factors:
        return "1"
    return " * ".join(compact_factor(factor, axis_names) for factor in factors)


def term_latex(term: Any, axis_names: list[str] | None = None) -> str:
    factors = list(getattr(term, "structure", None) or [])
    if not factors:
        return "1"
    return " ".join(factor_latex(factor, axis_names) for factor in factors)


# ------------------------------------------------------------------- equations


def _read_weights(equation: Any, attribute: str, flag: str) -> list[float] | None:
    """One weight vector, or ``None`` before it has been fitted.

    Both accessors raise when the equation has not been evaluated -- and in some
    EPDE builds print the whole equation on the way out -- so neither is ever
    reached except through here.
    """
    if not getattr(equation, flag, False):
        return None
    try:
        weights = getattr(equation, attribute)
    except Exception:  # noqa: BLE001
        return None
    try:
        return [float(value) for value in weights]
    except (TypeError, ValueError):
        return None


def equation_weights(equation: Any, term_count: int) -> tuple[list[float] | None, float | None]:
    """The term coefficients and the intercept, whichever way this build stores them.

    The right-hand side has no coefficient of its own, so there is always one
    coefficient fewer than there are terms. Where the *intercept* lives, though,
    changed between EPDE releases: 1.2.17 appends it to ``weights_final``, while
    master keeps ``weights_final`` at exactly the coefficient count and reads the
    intercept from ``weights_internal[-1]``.

    Assuming either layout silently corrupts the other. Reading master's vector
    as if it ended in an intercept drops the last real coefficient *and* reports
    it as a constant -- which turns ``u_tt = -9.87 u`` into ``u_tt = -9.87``: a
    well-formed, plausible, entirely wrong equation, with no error anywhere. So
    the layout is decided by length against the term count rather than by
    version, and an unrecognised length yields nothing rather than a guess.
    """
    final = _read_weights(equation, "weights_final", "weights_final_evald")
    internal = _read_weights(equation, "weights_internal", "weights_internal_evald")
    expected = max(term_count - 1, 0)

    if final is None:
        return None, None
    if len(final) == expected:
        intercept = internal[-1] if internal else None
        return final, intercept
    if len(final) == expected + 1:
        return final[:-1], final[-1]
    # Neither layout: report the equation as unfitted rather than attribute
    # coefficients to the wrong terms.
    return None, None


def _coefficient(coefficients: list[float] | None, term_index: int, target_index: int | None) -> float | None:
    """The coefficient of one term.

    Every index past the right-hand side shifts down by one, because the target
    occupies a position in the structure but not in the weight vector.
    """
    if coefficients is None or target_index is None or term_index == target_index:
        return None
    position = term_index if term_index < target_index else term_index - 1
    if 0 <= position < len(coefficients):
        return coefficients[position]
    return None


def describe_equation(
    equation: Any, *, prefix: str = "eq", axis_names: list[str] | None = None
) -> dict[str, Any]:
    """One equation of a system: its terms, coefficients, text and LaTeX."""
    terms = list(getattr(equation, "structure", None) or [])
    coefficients, intercept = equation_weights(equation, len(terms))
    target_index = getattr(equation, "target_idx", None)
    if not isinstance(target_index, int) or not (0 <= target_index < len(terms)):
        target_index = None

    described_terms: list[dict[str, Any]] = []
    for index, term in enumerate(terms):
        coefficient = _coefficient(coefficients, index, target_index)
        is_target = index == target_index
        described_terms.append(
            {
                "id": f"{prefix}:t{index}",
                "index": index,
                "name": compact_term(term, axis_names),
                "full_name": str(getattr(term, "name", "") or ""),
                "latex": term_latex(term, axis_names),
                "coefficient": coefficient,
                "is_target": is_target,
                # A term the sparse regression drove to zero is still carried in
                # the structure; saying so is what makes the equation readable.
                "active": is_target or (coefficient is not None and abs(coefficient) > ZERO_COEFFICIENT),
                "factors": [
                    {
                        "id": f"{prefix}:t{index}:f{factor_index}",
                        # The label a reader should see, with the dataset's own
                        # axis names. EPDE's positional form is kept alongside
                        # it: it is what the framework's own logs and any saved
                        # equation string will say, so losing it would make the
                        # two impossible to line up.
                        "label": _display_label(factor, axis_names),
                        "epde_label": str(getattr(factor, "label", "") or "?"),
                        "name": compact_factor(factor, axis_names),
                        "latex": factor_latex(factor, axis_names),
                        "family": str(getattr(factor, "ftype", "") or ""),
                        "variable": _variable_of(factor),
                        "is_deriv": bool(getattr(factor, "is_deriv", False)),
                        "deriv_code": _deriv_code(factor),
                        "params": factor_parameters(factor),
                    }
                    for factor_index, factor in enumerate(getattr(term, "structure", None) or [])
                ],
            }
        )

    variable = str(getattr(equation, "main_var_to_explain", "") or "")
    return {
        "variable": variable,
        "terms": described_terms,
        "target_term": f"{prefix}:t{target_index}" if target_index is not None else None,
        "intercept": intercept,
        "fitted": coefficients is not None,
        "text": equation_text(described_terms, intercept),
        "latex": equation_latex(described_terms, intercept),
        "epde_text": _safe(lambda: str(equation.text_form)),
        "metaparameters": _metaparameters(equation),
        "discrepancy": _safe_float(lambda: equation.fitness_value),
    }


def _variable_of(factor: Any) -> str:
    try:
        return str(factor.variable or "")
    except Exception:  # noqa: BLE001
        return str(getattr(factor, "ftype", "") or "")


def _deriv_code(factor: Any) -> list[int] | None:
    code = getattr(factor, "deriv_code", None)
    if code is None:
        return None
    try:
        return [int(axis) for axis in code if axis is not None]
    except TypeError:
        return None


def _metaparameters(equation: Any) -> dict[str, Any]:
    raw = getattr(equation, "metaparameters", None)
    if not isinstance(raw, dict):
        return {}
    described: dict[str, Any] = {}
    for key, value in raw.items():
        # Sparsity is keyed by a ``(name, variable)`` tuple, which JSON cannot
        # express as a key.
        name = ":".join(str(part) for part in key) if isinstance(key, tuple) else str(key)
        if isinstance(value, dict) and "value" in value:
            described[name] = _jsonable(value.get("value"))
        else:
            described[name] = _jsonable(value)
    return described


# -------------------------------------------------------------- rendered forms


def equation_text(terms: list[dict[str, Any]], intercept: float | None) -> str:
    """The equation as one line, with the right-hand side on the right.

    Built from the described terms rather than taken from EPDE's ``text_form``
    so that zero-weight terms can be left out -- an equation padded to the
    configured term count with ``0.0 *`` summands is the single biggest obstacle
    to reading a discovered model.
    """
    target = next((term for term in terms if term["is_target"]), None)
    left: list[str] = []
    for term in terms:
        if term["is_target"] or not term["active"]:
            continue
        coefficient = term["coefficient"]
        left.append(f"{_number(coefficient)} * {term['name']}")

    if intercept is not None and abs(intercept) > ZERO_COEFFICIENT:
        left.append(_number(intercept))
    if not left:
        left.append("0")

    right = target["name"] if target else "0"
    return " + ".join(left) + " = " + right


def equation_latex(terms: list[dict[str, Any]], intercept: float | None) -> str:
    target = next((term for term in terms if term["is_target"]), None)
    pieces: list[str] = []
    for term in terms:
        if term["is_target"] or not term["active"]:
            continue
        pieces.append(f"{_latex_number(term['coefficient'])} {term['latex']}")
    if intercept is not None and abs(intercept) > ZERO_COEFFICIENT:
        pieces.append(_latex_number(intercept))
    if not pieces:
        pieces.append("0")

    body = " + ".join(pieces).replace("+ -", "- ")
    right = target["latex"] if target else "0"
    return f"{right} = {body}"


def _number(value: float | None) -> str:
    if value is None:
        return "?"
    if value == 0:
        return "0"
    if 1e-3 <= abs(value) < 1e4:
        return f"{value:.4g}"
    return f"{value:.3e}"


def _latex_number(value: float | None) -> str:
    if value is None:
        return "?"
    if value == 0:
        return "0"
    if 1e-3 <= abs(value) < 1e4:
        return f"{value:.4g}"
    mantissa, exponent = f"{value:.3e}".split("e")
    return f"{mantissa} \\cdot 10^{{{int(exponent)}}}"


def _escape_latex(text: str) -> str:
    return r"\mathrm{" + text.replace("_", r"\_").replace("^", r"\^{}") + "}"


# --------------------------------------------------------------------- systems


def describe_system(
    system: Any,
    *,
    uid: str | None = None,
    objectives: list[float] | None = None,
    objective_names: list[str] | None = None,
    generation: int | None = None,
    axis_names: list[str] | None = None,
) -> dict[str, Any]:
    """A whole candidate system, ready to be sent to the browser.

    ``axis_names`` are the dataset's own coordinate names. EPDE numbers axes
    positionally, so without them a wave equation reads ``d^2u/dx1^2 =
    d^2u/dx2^2`` -- correct, and unrecognisable next to the equation the user
    is hoping to see.
    """
    variables = _variables_of(system)
    equations: list[dict[str, Any]] = []
    for index, variable in enumerate(variables):
        equation = _equation_for(system, variable, index)
        if equation is None:
            continue
        described = describe_equation(equation, prefix=f"e{index}", axis_names=axis_names)
        described.setdefault("variable", variable)
        if not described["variable"]:
            described["variable"] = variable
        equations.append(described)

    nodes, edges = _graph_of(equations, multiple=len(equations) > 1)
    active_terms = sum(1 for equation in equations for term in equation["terms"] if term["active"])

    return {
        "uid": uid or "",
        "generation": generation,
        "variables": variables,
        "equations": equations,
        "nodes": nodes,
        "edges": edges,
        "objectives": objectives,
        "objective_names": objective_names,
        "active_terms": active_terms,
        "complexity": _complexity(equations),
        "text": "\n".join(equation["text"] for equation in equations),
        "latex": _system_latex(equations),
    }


def empty_system(uid: str = "") -> dict[str, Any]:
    """The shape of a system with nothing in it, for an empty canvas."""
    return {
        "uid": uid,
        "generation": None,
        "variables": [],
        "equations": [],
        "nodes": [],
        "edges": [],
        "objectives": None,
        "objective_names": None,
        "active_terms": 0,
        "complexity": 0,
        "text": "",
        "latex": "",
    }


def compact_terms(system: Any, limit: int = 6, axis_names: list[str] | None = None) -> list[str]:
    """Short labels for a genealogy card: the active terms of the system.

    The counterpart of the operation names a FEDOT individual is labelled with.
    The right-hand side comes first, because it is what identifies the equation
    at a glance.
    """
    labels: list[str] = []
    for variable in _variables_of(system):
        equation = _equation_for(system, variable, 0)
        if equation is None:
            continue
        described = describe_equation(equation, axis_names=axis_names)
        target = next((term for term in described["terms"] if term["is_target"]), None)
        if target:
            labels.append(target["name"])
        labels.extend(
            term["name"]
            for term in described["terms"]
            if term["active"] and not term["is_target"]
        )
    return labels[:limit]


def _variables_of(system: Any) -> list[str]:
    variables = getattr(system, "vars_to_describe", None)
    if variables:
        return [str(name) for name in variables]
    chromosome = getattr(system, "vals", None)
    keys = getattr(chromosome, "equation_keys", None)
    return [str(key) for key in keys] if keys else []


def _equation_for(system: Any, variable: str, index: int) -> Any | None:
    chromosome = getattr(system, "vals", None)
    if chromosome is None:
        return None
    try:
        return chromosome[variable]
    except Exception:  # noqa: BLE001
        pass
    try:
        return list(system)[index]
    except Exception:  # noqa: BLE001
        return None


def _complexity(equations: list[dict[str, Any]]) -> int:
    """A structural size for the card: active terms plus the factors in them."""
    total = 0
    for equation in equations:
        for term in equation["terms"]:
            if term["active"]:
                total += 1 + max(len(term["factors"]) - 1, 0)
    return total


def _system_latex(equations: list[dict[str, Any]]) -> str:
    if not equations:
        return ""
    if len(equations) == 1:
        return equations[0]["latex"]
    body = r" \\ ".join(equation["latex"] for equation in equations)
    return r"\begin{cases}" + body + r"\end{cases}"


def _graph_of(
    equations: list[dict[str, Any]], *, multiple: bool
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Flatten the described system into the node/edge lists the canvas draws."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []

    root_id = "system"
    if multiple:
        nodes.append(
            {
                "id": root_id,
                "kind": "system",
                "label": "system",
                "latex": "",
                "variable": None,
                "coefficient": None,
                "active": True,
                "is_target": False,
                "params": {},
            }
        )

    for index, equation in enumerate(equations):
        equation_id = f"e{index}"
        nodes.append(
            {
                "id": equation_id,
                "kind": "equation",
                "label": equation["variable"] or f"equation {index + 1}",
                "latex": equation["latex"],
                "variable": equation["variable"],
                "coefficient": None,
                "active": True,
                "is_target": False,
                "params": {"intercept": equation["intercept"]},
            }
        )
        if multiple:
            edges.append({"source": root_id, "target": equation_id})

        for term in equation["terms"]:
            nodes.append(
                {
                    "id": term["id"],
                    "kind": "term",
                    "label": term["name"],
                    "latex": term["latex"],
                    "variable": equation["variable"],
                    "coefficient": term["coefficient"],
                    "active": term["active"],
                    "is_target": term["is_target"],
                    "params": {},
                }
            )
            edges.append({"source": equation_id, "target": term["id"]})

            for factor in term["factors"]:
                nodes.append(
                    {
                        "id": factor["id"],
                        "kind": "factor",
                        "label": factor["name"],
                        "latex": factor["latex"],
                        "variable": factor["variable"],
                        "coefficient": None,
                        "active": term["active"],
                        "is_target": False,
                        "params": factor["params"],
                        "family": factor["family"],
                        "is_deriv": factor["is_deriv"],
                    }
                )
                edges.append({"source": term["id"], "target": factor["id"]})

    return nodes, edges


# ------------------------------------------------------------------- utilities


def _safe(reader: Any) -> str | None:
    try:
        return reader()
    except Exception:  # noqa: BLE001
        return None


def _safe_float(reader: Any) -> float | None:
    try:
        value = float(reader())
    except Exception:  # noqa: BLE001
        return None
    return None if math.isnan(value) or math.isinf(value) else value


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)
