<?php
// Known public GH-24492 allocation contract question; not a security exploit.
// CI executes with memory_limit=16M, hard-limit-percent=200 and address-space cap.
register_shutdown_function(static function (): void { echo "FB_SHUTDOWN\n"; });
echo "FB_BEGIN\n";
// 14 MiB of source produces about 18.67 MiB of Base64 output.
$input = str_repeat("A", 14 * 1024 * 1024);
$result = base64_encode($input);
echo "FB_LENGTH=", strlen($result), "\n";
