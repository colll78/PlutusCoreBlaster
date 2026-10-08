import Lake
open Lake DSL

package PlutusCoreFacts where
  moreLeanArgs := #["--threads=2", "-s65536"]

require Blaster from git "https://github.com/colll78/Lean-blaster" @ "7f7c0248d64a7f52547bf498104f5775cdfb9fbb"
require PlutusCore from ".."

@[default_target]
lean_lib PlutusCoreFacts

@[test_driver]
lean_lib FactTests
