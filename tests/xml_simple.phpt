--TEST--
ForgeBlue baseline: XML extension smoke
--EXTENSIONS--
xml
--FILE--
<?php
$p = xml_parser_create();
var_dump(xml_parse($p, "<root><ok/></root>", true));
xml_parser_free($p);
?>
--EXPECT--
int(1)
