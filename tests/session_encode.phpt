--TEST--
ForgeBlue baseline: session serialization smoke
--EXTENSIONS--
session
--INI--
session.use_cookies=0
--FILE--
<?php
session_start();
$_SESSION["test"] = ["a" => 1];
$s = session_encode();
$_SESSION = [];
var_dump(session_decode($s));
var_dump($_SESSION["test"]["a"]);
session_abort();
?>
--EXPECT--
bool(true)
int(1)
