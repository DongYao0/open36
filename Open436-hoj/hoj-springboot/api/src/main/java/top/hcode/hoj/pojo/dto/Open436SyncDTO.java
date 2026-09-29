package top.hcode.hoj.pojo.dto;

import lombok.Data;

import java.io.Serializable;

/**
 * Open436 用户同步到 HOJ 的 DTO
 */
@Data
public class Open436SyncDTO implements Serializable {

    private static final long serialVersionUID = 1L;

    private String username;

    /**
     * 已绑定的 HOJ 用户 UUID。首次同步为空，后续同步必须以此作为身份依据。
     */
    private String hojUid;

    private String nickname;

    private String avatar;

    private String apiKey;

    /**
     * 用户角色（来自 Open436：admin / user）
     */
    private String role;
}
