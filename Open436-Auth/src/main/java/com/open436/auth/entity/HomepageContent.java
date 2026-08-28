package com.open436.auth.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;

/**
 * 首页内容表（Landing 3D 首页后台化管理）
 * 每个模块一行，content 列存完整 JSON（对象或数组），排序=数组下标顺序
 * module: about | experiences | technologies | works | feedbacks
 */
@Entity
@Table(name = "homepage_content")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class HomepageContent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 模块标识（唯一） */
    @Column(unique = true, nullable = false, length = 50)
    private String module;

    /** 模块完整内容 JSON（jsonb 列，JDBC 层按 JSON 写入避免 varchar/jsonb 类型不匹配） */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false, columnDefinition = "jsonb")
    private String content;

    /** 最后修改人 */
    @Column(name = "updated_by")
    private Long updatedBy;

    /** 最后修改时间 */
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
