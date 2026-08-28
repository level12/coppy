- Make `mise run upgrade-deps` upgrade the mise tools, not just update
  `mise.lock`. This ensures the tools in the updated lock file are immediately available
  after the upgrade task finishes.
