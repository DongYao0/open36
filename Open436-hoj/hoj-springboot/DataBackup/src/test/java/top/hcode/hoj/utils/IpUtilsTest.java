package top.hcode.hoj.utils;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

class IpUtilsTest {

    @Test
    void readsCloudflareAddressFirst() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("CF-Connecting-IP", "203.0.113.8");
        request.addHeader("X-Forwarded-For", "198.51.100.2");

        assertEquals("203.0.113.8", IpUtils.getUserIpAddr(request));
    }

    @Test
    void skipsInvalidProxyEntries() {
        assertEquals("198.51.100.7", IpUtils.firstValid("unknown, forged-value, 198.51.100.7"));
    }

    @Test
    void acceptsBracketedIpv6WithPort() {
        assertEquals("2001:db8::1", IpUtils.firstValid("[2001:db8::1]:443"));
    }

    @Test
    void stripsIpv4Port() {
        assertEquals("192.0.2.5", IpUtils.firstValid("192.0.2.5:8080"));
    }

    @Test
    void fallsBackToRemoteAddress() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Forwarded-For", "not-an-ip");
        request.setRemoteAddr("2001:db8::9");

        assertEquals("2001:db8::9", IpUtils.getUserIpAddr(request));
    }

    @Test
    void rejectsOversizedOrInvalidInput() {
        assertNull(IpUtils.firstValid("999.999.999.999"));
        assertNull(IpUtils.firstValid("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"));
    }
}
