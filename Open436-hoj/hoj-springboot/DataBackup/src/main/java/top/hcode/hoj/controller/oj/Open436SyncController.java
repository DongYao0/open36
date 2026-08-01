package top.hcode.hoj.controller.oj;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import top.hcode.hoj.annotation.AnonApi;
import top.hcode.hoj.common.exception.StatusFailException;
import top.hcode.hoj.common.result.CommonResult;
import top.hcode.hoj.manager.oj.Open436SyncManager;
import top.hcode.hoj.pojo.dto.Open436SyncDTO;
import top.hcode.hoj.pojo.vo.UserInfoVO;
import top.hcode.hoj.utils.JwtUtils;

import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;

/**
 * Open436 用户同步接口
 * 供 Open436 认证服务调用，实现 SSO
 */
@RestController
@RequestMapping("/api")
public class Open436SyncController {

    @Autowired
    private Open436SyncManager open436SyncManager;

    @Autowired
    private JwtUtils jwtUtils;

    @PostMapping("/open436-sync")
    @AnonApi
    public CommonResult<UserInfoVO> sync(@Valid @RequestBody Open436SyncDTO dto,
                                          HttpServletResponse response) {
        try {
            UserInfoVO userInfoVO = open436SyncManager.sync(dto);
            String jwt = jwtUtils.generateToken(userInfoVO.getUid());
            response.setHeader("Authorization", jwt);
            response.setHeader("Access-Control-Expose-Headers", "Authorization");
            return CommonResult.successResponse(userInfoVO, "同步成功");
        } catch (StatusFailException e) {
            return CommonResult.errorResponse(e.getMessage());
        }
    }
}
