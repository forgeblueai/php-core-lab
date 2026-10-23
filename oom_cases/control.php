<?php
register_shutdown_function(static function (): void { echo "FB_SHUTDOWN\n"; });
echo "FB_BEGIN\n";
echo "FB_LENGTH=", strlen(str_repeat("A", 1000)), "\n";
