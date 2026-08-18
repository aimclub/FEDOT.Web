"""EPDE.Web — a web interface for the EPDE differential-equation discovery framework.

The package is self-contained: it shares no code with ``fedotweb`` and imports
neither FEDOT nor GOLEM. EPDE does not use GOLEM, so everything GOLEM would have
provided — individual identity, ancestry, a per-generation callback, a saved
optimisation history — is supplied here by :mod:`epdeweb.adapters`.

``epde`` itself is imported only inside the run worker, so a server can start,
serve its API and browse finished runs on a machine where EPDE is not installed.
"""

__version__ = "0.1.0"
