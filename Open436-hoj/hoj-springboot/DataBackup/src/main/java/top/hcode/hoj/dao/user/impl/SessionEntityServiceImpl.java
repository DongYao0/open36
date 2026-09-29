package top.hcode.hoj.dao.user.impl;

import cn.hutool.core.date.DateUtil;
import cn.hutool.http.HttpUtil;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import top.hcode.hoj.mapper.SessionMapper;
import top.hcode.hoj.mapper.UserInfoMapper;
import top.hcode.hoj.pojo.entity.msg.AdminSysNotice;
import top.hcode.hoj.pojo.entity.user.Session;
import top.hcode.hoj.pojo.entity.msg.UserSysNotice;
import top.hcode.hoj.dao.msg.AdminSysNoticeEntityService;
import top.hcode.hoj.dao.msg.UserSysNoticeEntityService;
import top.hcode.hoj.dao.user.SessionEntityService;

import javax.annotation.Resource;
import java.util.Date;
import java.util.List;
import java.util.Objects;

/**
 * @Author: Himit_ZH
 * @Date: 2020/12/3 22:46
 * @Description:
 */
@Slf4j
@Service
public class SessionEntityServiceImpl extends ServiceImpl<SessionMapper, Session> implements SessionEntityService {

    @Resource
    private SessionMapper sessionMapper;

    @Resource
    private UserInfoMapper userInfoMapper;

    @Resource
    private AdminSysNoticeEntityService adminSysNoticeEntityService;

    @Resource
    private UserSysNoticeEntityService userSysNoticeEntityService;

    @Override
    @Async
    public void checkRemoteLogin(String uid) {
        QueryWrapper<Session> sessionQueryWrapper = new QueryWrapper<>();
        sessionQueryWrapper.eq("uid", uid)
                .orderByDesc("gmt_create")
                .last("limit 2");
        List<Session> sessionList = sessionMapper.selectList(sessionQueryWrapper);
        if (sessionList.size() < 2) {
            return;
        }
        Session nowSession = sessionList.get(0);
        Session lastSession = sessionList.get(1);
        // 如果两次登录的ip不相同，需要发通知给用户
        if (!Objects.equals(nowSession.getIp(), lastSession.getIp())) {
            // 通知属于非核心功能：任何失败都必须降级忽略，绝不能影响登录本身
            AdminSysNotice adminSysNotice = null;
            try {
                String remoteLoginContent = getRemoteLoginContent(lastSession.getIp(), nowSession.getIp(), nowSession.getGmtCreate());
                if (remoteLoginContent == null) {
                    return;
                }
                adminSysNotice = new AdminSysNotice();
                adminSysNotice
                        .setType("Single")
                        .setContent(remoteLoginContent)
                        .setTitle("账号异地登录通知(Account Remote Login Notice)")
                        // admin_id 外键指向 user_info(uuid)：必须写真实 uuid，
                        // 不能写 "1"（历史缺陷，会触发 admin_sys_notice_ibfk_2 外键错误）。
                        // 查不到超级管理员时写 NULL（列可空，外键允许）。
                        .setAdminId(resolveNoticeAdminUid())
                        .setState(false)
                        .setRecipientId(uid);
                boolean isSaveOk = adminSysNoticeEntityService.save(adminSysNotice);
                if (isSaveOk) {
                    UserSysNotice userSysNotice = new UserSysNotice();
                    userSysNotice.setType("Sys")
                            .setSysNoticeId(adminSysNotice.getId())
                            .setRecipientId(uid)
                            .setState(false);
                    boolean isOk = userSysNoticeEntityService.save(userSysNotice);
                    if (isOk) {
                        adminSysNotice.setState(true);
                        if (!adminSysNoticeEntityService.updateById(adminSysNotice)) {
                            throw new IllegalStateException("异地登录通知状态更新失败");
                        }
                    } else {
                        if (!adminSysNoticeEntityService.removeById(adminSysNotice.getId())) {
                            throw new IllegalStateException("异地登录半成品通知清理失败");
                        }
                    }
                }
            } catch (Exception e) {
                cleanupIncompleteNotice(adminSysNotice, uid);
                log.warn("异地登录通知写入失败，已降级忽略（不影响登录）。uid={}, err={}", uid, e.getMessage(), e);
            }
        }
    }

    /**
     * 解析异地登录通知的发送者（超级管理员 uuid）。
     *
     * @return 真实存在的超级管理员 uuid；查不到时返回 {@code null}
     */
    private String resolveNoticeAdminUid() {
        try {
            List<String> superAdmins = userInfoMapper.getSuperAdminUidList();
            if (superAdmins != null && !superAdmins.isEmpty()) {
                return superAdmins.get(0);
            }
        } catch (Exception e) {
            log.warn("查询超级管理员失败，异地登录通知将不写发送者：{}", e.getMessage());
        }
        return null;
    }

    private void cleanupIncompleteNotice(AdminSysNotice notice, String uid) {
        if (notice == null || notice.getId() == null) {
            return;
        }
        try {
            // user_sys_notice 由外键级联删除，避免定时任务再次分发半成品。
            adminSysNoticeEntityService.removeById(notice.getId());
        } catch (Exception cleanupError) {
            log.error("清理异地登录半成品通知失败。uid={}, noticeId={}", uid, notice.getId(), cleanupError);
        }
    }

    private String getRemoteLoginContent(String oldIp, String newIp, Date loginDate) {
        String dateStr = DateUtil.format(loginDate, "yyyy-MM-dd HH:mm:ss");
        StringBuilder sb = new StringBuilder();
        sb.append("亲爱的用户，您好！您的账号于").append(dateStr);
        String addr = null;
        try {
            String newRes = HttpUtil.get("https://whois.pconline.com.cn/ipJson.jsp?ip=" + newIp + "&json=true");
            JSONObject newResJson = JSONUtil.parseObj(newRes);
            addr = newResJson.getStr("addr");

            String newCityCode = newResJson.getStr("cityCode");

            String oldRes = HttpUtil.get("https://whois.pconline.com.cn/ipJson.jsp?ip=" + oldIp + "&json=true");
            JSONObject oldResJson = JSONUtil.parseObj(oldRes);

            String oldCityCode = oldResJson.getStr("cityCode");

            if (newCityCode == null || oldCityCode == null || newCityCode.equals(oldCityCode)) {
                return null;
            }

        } catch (Exception ignored) {
            return null;
        }
        if (!StringUtils.isEmpty(addr)) {
            sb.append("在【")
                    .append(addr)
                    .append("】");
        }
        sb.append("登录，登录IP为：【")
                .append(newIp)
                .append("】，若非本人操作，请立即修改密码。")
                .append("\n\n")
                .append("Hello! Dear user, Your account was logged in in");

        if (!StringUtils.isEmpty(addr)) {
            sb.append(" 【")
                    .append(addr)
                    .append("】 on ")
                    .append(dateStr)
                    .append(". If you do not operate by yourself, please change your password immediately.");
        }

        return sb.toString();
    }
}
