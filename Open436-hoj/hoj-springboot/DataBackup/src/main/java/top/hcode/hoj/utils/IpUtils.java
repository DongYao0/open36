package top.hcode.hoj.utils;

import lombok.extern.slf4j.Slf4j;

import javax.servlet.http.HttpServletRequest;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.regex.Pattern;

/**
 * @Author: Himit_ZH
 * @Date: 2020/10/30 11:12
 * @Description: 客户端 IP 解析。
 *
 * <p>Open436 加固说明（2026-09-29）：
 * <ul>
 *   <li>提交接口曾出现 {@code Data too long for column 'ip'}，导致提交记录写入失败。
 *       根因是 {@code judge.ip} 为 {@code varchar(20)}，且解析结果未经校验、未限长。</li>
 *   <li>本类现在保证：任何输入都只返回「合法 IPv4/IPv6」或安全占位值，长度绝不超过
 *       {@link #MAX_IP_LENGTH}，且绝不抛异常。</li>
 *   <li>IP 解析失败绝不能阻断提交保存。</li>
 * </ul>
 */
@Slf4j(topic = "hoj")
public class IpUtils {

    /** judge.ip 列宽；IPv4-mapped IPv6 最长形式为 45 字符。 */
    public static final int MAX_IP_LENGTH = 45;

    /** 无法解析时写入的安全占位值，保证非空且合法。 */
    public static final String UNKNOWN_IP = "0.0.0.0";

    private static final Pattern IPV4_PATTERN = Pattern.compile(
            "^((25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)\\.){3}(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)$");

    private static final Pattern IPV6_PATTERN = Pattern.compile(
            "^("
                    + "([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|"
                    + "([0-9a-fA-F]{1,4}:){1,7}:|"
                    + "([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
                    + "([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
                    + "([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
                    + "([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|"
                    + "([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
                    + "[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
                    + ":((:[0-9a-fA-F]{1,4}){1,7}|:)|"
                    + "::(ffff(:0{1,4})?:)?"
                    + "((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\\.){3}(25[0-5]|(2[0-4]|1?[0-9])?[0-9])|"
                    // 完全展开的 IPv4-mapped 形式：x:x:x:x:x:x:d.d.d.d（最长 45 字符）
                    + "([0-9a-fA-F]{1,4}:){6}"
                    + "((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\\.){3}(25[0-5]|(2[0-4]|1?[0-9])?[0-9])|"
                    + "([0-9a-fA-F]{1,4}:){1,4}:"
                    + "((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\\.){3}(25[0-5]|(2[0-4]|1?[0-9])?[0-9])"
                    + ")$");

    /**
     * 解析客户端真实 IP。
     *
     * <p>优先级：Cloudflare 可信头 → X-Forwarded-For 首个有效地址 → X-Real-IP
     * → 其他代理头 → 真实连接地址。任一环节异常都退化为 {@link #UNKNOWN_IP}。
     */
    public static String getUserIpAddr(HttpServletRequest request) {
        try {
            String ip = firstValid(request.getHeader("CF-Connecting-IP"));
            if (ip == null) {
                ip = firstValid(request.getHeader("X-Forwarded-For"));
            }
            if (ip == null) {
                ip = firstValid(request.getHeader("X-Real-IP"));
            }
            if (ip == null) {
                ip = firstValid(request.getHeader("Proxy-Client-IP"));
            }
            if (ip == null) {
                ip = firstValid(request.getHeader("WL-Proxy-Client-IP"));
            }
            if (ip == null) {
                ip = firstValid(request.getRemoteAddr());
            }
            return ip == null ? UNKNOWN_IP : ip;
        } catch (Exception e) {
            // 绝不能因为取 IP 失败而阻断业务（例如提交落库）
            log.warn("用户 IP 解析失败，已写入占位值 {}", UNKNOWN_IP, e);
            return UNKNOWN_IP;
        }
    }

    /**
     * 从可能包含代理链、端口、方括号、引号或超长内容的原始头值中，提取第一个合法 IP。
     *
     * @return 合法 IP 字符串；无法解析时返回 {@code null}
     */
    static String firstValid(String raw) {
        if (raw == null) {
            return null;
        }
        // 代理链按顺序取第一个合法地址；恶意或损坏的首项不能遮蔽后续合法地址。
        for (String candidate : raw.split(",")) {
            String value = normalizeCandidate(candidate);
            if (value != null) {
                return value;
            }
        }
        return null;
    }

    private static String normalizeCandidate(String candidate) {
        String value = candidate.trim();
        if (value.isEmpty() || "unknown".equalsIgnoreCase(value)) {
            return null;
        }
        value = stripQuotes(value);
        value = stripBracketsAndPort(value);
        value = stripIpv4Port(value);
        if (value.isEmpty() || !isValidIp(value)) {
            return null;
        }
        // 合法 IPv4/IPv6 天然不超过列宽；保留检查防止未来校验规则被放宽。
        return value.length() <= MAX_IP_LENGTH ? value : null;
    }

    private static String stripQuotes(String value) {
        if (value.length() >= 2
                && ((value.charAt(0) == '"' && value.charAt(value.length() - 1) == '"')
                || (value.charAt(0) == '\'' && value.charAt(value.length() - 1) == '\''))) {
            return value.substring(1, value.length() - 1).trim();
        }
        return value;
    }

    /** 处理 {@code [2001:db8::1]:443} 与 {@code [2001:db8::1]} 形式。 */
    private static String stripBracketsAndPort(String value) {
        if (value.startsWith("[")) {
            int close = value.indexOf(']');
            if (close > 0) {
                return value.substring(1, close);
            }
        }
        return value;
    }

    /** 处理 {@code 1.2.3.4:5678} 形式；IPv6 含多个冒号，不做端口剥离。 */
    private static String stripIpv4Port(String value) {
        int colon = value.indexOf(':');
        if (colon > 0 && value.indexOf(':', colon + 1) < 0) {
            return value.substring(0, colon);
        }
        return value;
    }

    /**
     * 纯词法校验，不做任何 DNS 解析——避免被伪造的超长/恶意头触发名称解析。
     */
    private static boolean isValidIp(String value) {
        return IPV4_PATTERN.matcher(value).matches() || IPV6_PATTERN.matcher(value).matches();
    }

    public static String getServiceIp() {
        InetAddress address = null;
        try {
            address = InetAddress.getLocalHost();
            return address.getHostAddress(); //返回IP地址
        } catch (UnknownHostException e) {
            log.error("本地ip获取异常---------->{}", e.getMessage());
        }
        return null;
    }
}
