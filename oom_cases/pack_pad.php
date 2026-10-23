<?php
// Related public issue: php/php-src#24492.
register_shutdown_function(static function (): void { echo "FB_SHUTDOWN\n"; });
echo "FB_BEGIN\n";
$result = pack("x40000000");
echo "FB_LENGTH=", strlen($result), "\n";
