<?php
// Related public issue: php/php-src#24492; upstream PR #24596.
register_shutdown_function(static function (): void { echo "FB_SHUTDOWN\n"; });
echo "FB_BEGIN\n";
$input = str_repeat("\0", 12 * 1024 * 1024);
$result = urlencode($input);
echo "FB_LENGTH=", strlen($result), "\n";
