package com.open436.auth.file;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

import java.io.IOException;
import java.util.Map;

/**
 * 文件服务客户端
 * 调用 Rust FileService 进行文件上传
 */
@Slf4j
@Component
public class FileServiceClient {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${file.service.url:http://localhost:8007}")
    private String fileServiceUrl;

    /**
     * 上传文件到 FileService
     *
     * @param file MultipartFile
     * @param fileType 文件类型 (avatar, post, resource 等)
     * @return 上传后的 URL
     */
    public String uploadFile(MultipartFile file, String fileType) throws IOException {
        return uploadFile(file, fileType, null);
    }

    /**
     * 上传文件到 FileService（透传用户身份）
     *
     * @param file MultipartFile
     * @param fileType 文件类型 (avatar, post, resource 等)
     * @param userId 上传者用户ID（写入 X-User-Id 供 FileService 记录 uploader）
     * @return 上传后的 URL
     */
    public String uploadFile(MultipartFile file, String fileType, Long userId) throws IOException {
        String uploadUrl = fileServiceUrl + "/api/files/upload";

        // 将 MultipartFile 转换为 ByteArrayResource
        byte[] bytes = file.getBytes();
        ByteArrayResource resource = new ByteArrayResource(bytes) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };

        // 构建 multipart 请求
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", resource);
        body.add("file_type", fileType);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        if (userId != null) {
            headers.set("X-User-Id", String.valueOf(userId));
        }

        HttpEntity<MultiValueMap<String, Object>> entity = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                uploadUrl,
                HttpMethod.POST,
                entity,
                Map.class
            );

            if (response.getBody() != null) {
                Map<String, Object> responseBody = response.getBody();
                // FileService 上传成功返回 code 200（新）或 201（旧版/容器镜像），均视为成功
                Integer code = (Integer) responseBody.get("code");
                if (code != null && (code == 200 || code == 201)) {
                    Map<String, Object> data = (Map<String, Object>) responseBody.get("data");
                    if (data != null && data.get("url") != null) {
                        return data.get("url").toString();
                    }
                }
                String message = (String) responseBody.get("message");
                throw new RuntimeException("File upload failed: " + message);
            }
            throw new RuntimeException("File upload failed: empty response");
        } catch (Exception e) {
            log.error("文件上传失败: {}", e.getMessage(), e);
            throw new RuntimeException("文件上传失败: " + e.getMessage());
        }
    }
}
