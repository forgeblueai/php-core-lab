--TEST--
Base64 encoding retains correct data on empty, short, long, binary inputs
--FILE--
<?php
foreach (["", "f", "fo", "foo", "hello\0world", str_repeat("x", 2048)] as $s) {
    var_dump(base64_decode(base64_encode($s), true) === $s);
}
?>
--EXPECT--
bool(true)
bool(true)
bool(true)
bool(true)
bool(true)
bool(true)
