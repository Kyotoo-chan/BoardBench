# Abalone v3 setup-emphasis findings

The v2 setup-emphasis implementation is unchanged. Under v3 it passes all 33 clear-rule scenarios and all 4 scored human-decision scenarios.

The v2 `ABAL-R19` forced-pass miss is not a v3 scenario failure. The publisher packet does not decide that case. Judges from v2 may still mention empty `legal_actions` in the constructed no-move state.
