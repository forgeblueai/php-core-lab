--TEST--
GH-24492 Base64 helper consumers remain functional under ordinary allocation
--EXTENSIONS--
openssl
iconv
soap
--FILE--
<?php
$hash = password_hash('secret', PASSWORD_BCRYPT, ['cost' => 4]);
var_dump(is_string($hash) && password_verify('secret', $hash));

$key = str_repeat('K', 16);
$iv = str_repeat("\0", 16);
$encrypted = openssl_encrypt('payload', 'aes-128-cbc', $key, 0, $iv);
var_dump(is_string($encrypted)
    && openssl_decrypt($encrypted, 'aes-128-cbc', $key, 0, $iv) === 'payload');

$subject = iconv_mime_encode('Subject', 'Café', [
    'scheme' => 'B',
    'input-charset' => 'UTF-8',
    'output-charset' => 'UTF-8',
]);
var_dump(is_string($subject) && str_contains($subject, '=?UTF-8?B?'));

class OfflineBase64Soap extends SoapClient
{
    public string $captured = '';
    public function __doRequest(
        string $request, string $location, string $action, int $version,
        bool $oneWay = false, ?string $uriParserClass = null
    ): ?string {
        $this->captured = $request;
        return '';
    }
}
$client = new OfflineBase64Soap(null, [
    'location' => 'http://127.0.0.1/unused',
    'uri' => 'urn:offline',
    'exceptions' => true,
]);
try {
    $client->__soapCall('echo', [new SoapVar('abc', XSD_BASE64BINARY)]);
} catch (SoapFault $ignored) {
    // Expected; no network request is issued because __doRequest is overridden.
}
var_dump(str_contains($client->captured, 'YWJj'));
?>
--EXPECT--
bool(true)
bool(true)
bool(true)
bool(true)
