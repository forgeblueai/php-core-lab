--TEST--
ForgeBlue baseline: Zend basic execution
--FILE--
<?php
function fb_add(int $a, int $b): int { return $a + $b; }
var_dump(fb_add(3, 4));
var_dump(array_sum([1, 2, 3]));
?>
--EXPECT--
int(7)
int(6)
