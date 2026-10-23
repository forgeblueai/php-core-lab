<?php
// Bounded string-allocation behavior probe.
register_shutdown_function(static function (): void { echo "FB_SHUTDOWN\n"; });
echo "FB_BEGIN\n";
$input = str_repeat("x", 14 * 1024 * 1024);
$result = bin2hex($input);
echo "FB_LENGTH=", strlen($result), "\n";
