# LEAN integration boundary

Status: **prepared_not_validated**. The app uses vectorbt; it does not run LEAN and never labels another engine's result as LEAN. A future isolated engine must consume immutable strategy/data manifests, preserve signal/fill time, and normalize results with the exact engine version.

No QuantConnect account, CLI, engine runtime or broker connection is required by the current demo. Manifest conversion, run/cancel capabilities and comparison acceptance are not implemented yet. An unavailable option must return a clear EngineUnavailable error when an actual integration endpoint is introduced.
