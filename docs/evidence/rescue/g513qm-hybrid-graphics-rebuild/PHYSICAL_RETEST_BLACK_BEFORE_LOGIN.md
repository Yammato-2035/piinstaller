# Black freeze before login (operator report)

After rescue-KMS Hybrid default, operator reported freeze to black screen **before** being able to type at login.

## Conclusion

AMD-KMS Hybrid/AMD-Safe remain unsafe as default on Gabriel. Revert GRUB default to **Basic Emergency (nomodeset + rescue.target)** — the only profile that previously reached a login prompt.

Login when prompt appears: `root` + Enter (empty), not `Mint`.
