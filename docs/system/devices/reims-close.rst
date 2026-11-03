Reims window close controls (local fork)
=======================================

``apple-gfx-pci`` and ``apple-gfx-mmio`` accept ``close-action``:

* ``poweroff`` (also the unset default) retains QEMU's immediate poweroff.
* ``powerdown`` requests the guest's normal ACPI shutdown. Repeated window
  close requests never escalate to immediate poweroff. An unsaved document
  or guest policy can delay or refuse shutdown.
* ``suspend`` requests a guest-cooperative sleep button. On q35, opt into
  its fixed ACPI sleep button with ``-global ICH9-LPC.x-sleep-button=on``.
  The guest must enable the button event and enter S3 itself. No enabled
  button leaves the guest running, with a diagnostic. A later close can
  retry a button press that the guest handled without entering sleep.

Actual guest S3, after the vCPUs stop, drains and pauses the retained Reims
GPU device. Its resources and guest RAM stay in this process. The S3 wake
reset preserves the paused device; the wake notifier unpauses it before
vCPUs resume. The window displays Suspended while asleep. QMP
``system_wakeup`` resumes the guest and requests restore/raise of the same
window, subject to compositor focus policy. These actions never request
Linux host suspend. The configured guest RAM remains allocated during S3.

This is not save-to-disk: apple-gfx still blocks migration. A hung GPU can
prevent the pause drain from completing. Suspend requires repeated real
guest qualification before a launcher selects it. A launcher should select
``powerdown`` when guest S3 fails its tests. Wake a suspended guest before
requesting clean shutdown. Never substitute QMP ``stop`` or a direct
``qemu_system_suspend_request`` for guest preparation.

These changes target this private desktop fork, not upstream QEMU.
