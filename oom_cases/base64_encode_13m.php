<?php
// Differential probe: 13 MiB input at the same 16 MiB soft / 32 MiB hard limits.
// Known GH-24492 research only; a process-local bounded memory test.
register_shutdown_function(static function (): void { echo "FB_SHUTDOWN\n"; });
echo "FB_BEGIN\n";
$input = str_repeat("A", 13 * 1024 * 1024);
echo "FB_INPUT_READY\n";
$result = base64_encode($input);
echo "FB_LENGTH=", strlen($result), "\n";
