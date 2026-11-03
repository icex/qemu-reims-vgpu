/* Local experiment; GPL-2.0-or-later. Standalone, never opens /dev/kvm. */
#include "../../accel/kvm/halt-poll.h"
#include <assert.h>
#include <stdio.h>
struct Mock { int calls; int supported; int result; uint64_t ns; };
static int mock(void *opaque, unsigned long request, uintptr_t arg)
{
    struct Mock *m = opaque;
    m->calls++;
    if (request == KVM_CHECK_EXTENSION) {
        assert(arg == KVM_CAP_HALT_POLL);
        return m->supported;
    }
    assert(request == KVM_ENABLE_CAP);
    struct kvm_enable_cap *cap = (void *)arg;
    assert(cap->cap == KVM_CAP_HALT_POLL && cap->flags == 0);
    assert(cap->args[0] == m->ns);
    assert(cap->args[1] == 0 && cap->args[2] == 0 && cap->args[3] == 0);
    for (unsigned i = 0; i < sizeof(cap->pad); i++) { assert(cap->pad[i] == 0); }
    return m->result;
}
int main(void)
{
    struct Mock m = { .supported = 1 };
    assert(kvm_apply_halt_poll(false, 0, mock, &m) == 0 && m.calls == 0);
    assert(kvm_apply_halt_poll(true, 0, mock, &m) == 0 && m.calls == 2);
    m.ns = UINT64_MAX;
    assert(kvm_apply_halt_poll(true, m.ns, mock, &m) == 0 && m.calls == 4);
    m.result = -EINVAL;
    assert(kvm_apply_halt_poll(true, m.ns, mock, &m) == -EINVAL);
    m.supported = 0; m.calls = 0;
    assert(kvm_apply_halt_poll(true, 0, mock, &m) == -ENOTSUP && m.calls == 1);
    m.supported = -EBADF;
    assert(kvm_apply_halt_poll(true, 0, mock, &m) == -EBADF && m.calls == 2);
    puts("PASS: omitted, zero, uint64, enable-error, absent-cap, check-error");
}
