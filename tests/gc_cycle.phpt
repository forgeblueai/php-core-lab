--TEST--
ForgeBlue baseline: cyclic object teardown
--FILE--
<?php
class FBRing { public mixed $next = null; }
$a = new FBRing(); $b = new FBRing();
$a->next = $b; $b->next = $a;
unset($a, $b);
var_dump(gc_collect_cycles() >= 2);
?>
--EXPECT--
bool(true)
