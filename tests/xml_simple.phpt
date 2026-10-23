--TEST--
ForgeBlue baseline: XML extension smoke across PHP 8.4 and 8.5
--EXTENSIONS--
xml
--FILE--
<?php
$p = xml_parser_create();
var_dump(xml_parse($p, "<root><ok/></root>", true));
// xml_parser_free() is a no-op since PHP 8.0 and deprecated since PHP 8.5.
unset($p);
?>
--EXPECT--
int(1)
