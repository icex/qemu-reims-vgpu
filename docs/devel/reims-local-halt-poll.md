# Local per-VM halt-poll control

This fork retains DAILY fixes from 04ba2a21f365 and the I-tested per-VM
KVM halt-poll control. Fork-local use only; no upstream
submission or Signed-off-by representation. QEMU AGENTS/code-provenance permit
local experiments not intended for upstream contribution.

Launcher option: replace the existing KVM accelerator argument with
`-accel kvm,halt-poll-ns=0` for polling off, or e.g. `halt-poll-ns=50000` for 50us.
Never add a second accelerator selection to an existing launcher. Omit the property
for unchanged kernel policy. No environment hook changes the user's launcher.
The uint64 property rejects negative/malformed inputs via QOM's uint64 visitor;
property changes after KVM initialization are rejected. Extreme positive values
are passed to the kernel, whose refusal fails initialization, not silently ignored.

Explicit zero differs from omitted: a separate boolean controls whether any ioctl
is made. Initial creation AND VM-fd reconstruction apply KVM_CAP_HALT_POLL before
vCPU creation/rebinding. Missing capability and ioctl errors fail with negative
errno. Reconstruction closes the newly owned VM fd on this failure; initial
creation uses kvm_init's existing error cleanup. No global module parameter,
security, scheduling or unrelated VM changes. No KVM open in unit tests.

API source verified in the Linux KVM API documentation section 7.20:
https://www.kernel.org/doc/html/next/virt/kvm/api.html#kvm-cap-halt-poll
It specifies VM scope and args[0] in ns, with zero success and error on failure.

Standalone test compiles the ACTUAL integration helper with a mock ioctl and
checks omitted/no calls, zero, UINT64_MAX, full zero-filled capability struct,
enable error, unsupported cap and check error. No VM/device/kernel interaction.
QOM parsing and full integration compilation remain separate deferred checks;
no QEMU executable is run under the prep prohibition, even for '-help'.

Historical tiny-KVM 8.54x vCPU CPU ratio and GPUloop -17.91% CPU/1.82x worse ACK p99
are not a desktop speedup or latency approval. Later A/B must measure both.
