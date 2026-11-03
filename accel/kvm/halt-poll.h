/* Local experiment; GPL-2.0-or-later. No KVM access in the policy helper. */
#ifndef REIMS_KVM_HALT_POLL_H
#define REIMS_KVM_HALT_POLL_H
#include <stdbool.h>
#include <stdint.h>
#include <errno.h>
#include <linux/kvm.h>
#include <sys/ioctl.h>

typedef int (*KvmHaltPollIoctl)(void *, unsigned long, uintptr_t);

static inline int kvm_apply_halt_poll(bool specified, uint64_t ns,
                                     KvmHaltPollIoctl call, void *opaque)
{
    struct kvm_enable_cap cap = { .cap = KVM_CAP_HALT_POLL };
    int ret;
    if (!specified) {
        return 0;
    }
    ret = call(opaque, KVM_CHECK_EXTENSION, KVM_CAP_HALT_POLL);
    if (ret <= 0) {
        return ret < 0 ? ret : -ENOTSUP;
    }
    cap.args[0] = ns;
    return call(opaque, KVM_ENABLE_CAP, (uintptr_t)&cap);
}
#endif
