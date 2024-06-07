package ai.scaia.azure;/*
 *@created 04/06/2024- 12:08
 *@author neha
 */

import ai.scaia.config.Config;
import ai.scaia.result.ProcessingResult;
import com.azure.storage.blob.BlobClient;
import com.azure.storage.blob.BlobClientBuilder;
import com.azure.storage.blob.BlobContainerClient;
import com.azure.storage.blob.BlobContainerClientBuilder;
import lombok.extern.slf4j.Slf4j;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.util.List;
import java.util.Objects;

@Slf4j
public class AzureBlobStorageService {

    private static final String CONNECTION_STRING = Config.getProperty("azure.blob.connectionString");
    private static final String INPUT_CONTAINER_NAME = Config.getProperty("azure.blob.inputcontainer");
    private static final String OUTPUT_CONTAINER_NAME = Config.getProperty("azure.blob.outputcontainer");
    private static final String DOWNLOAD_PATH = Config.getProperty("azure.blob.downloadpath");

    public static void uploadData(String blob, String fileName) {
        BlobClient blobClient = new BlobClientBuilder()
                .connectionString(CONNECTION_STRING)
                .containerName(OUTPUT_CONTAINER_NAME)
                .blobName(fileName)
                .buildClient();

        try (InputStream dataStream = new ByteArrayInputStream(blob.getBytes(StandardCharsets.UTF_8))) {
            blobClient.upload(dataStream, blob.getBytes(StandardCharsets.UTF_8).length, true);
            ProcessingResult.successResults.add("Successfully uploaded " + fileName + " to " + OUTPUT_CONTAINER_NAME);
        } catch (IOException ex) {
            ProcessingResult.failureResults.add(String.format("Failed to upload file %s and exception is %s", fileName, ex.getMessage()));
            log.error("ignoring upload error for file {}, to continue processing {}", fileName, ex.getMessage());
        }
    }

    public static List<File> downloadData() {
        BlobContainerClient containerClient = new BlobContainerClientBuilder()
                .connectionString(CONNECTION_STRING)
                .containerName(INPUT_CONTAINER_NAME)
                .buildClient();

        return containerClient.listBlobs().stream().map(b -> downloadBlob(containerClient, b.getName())).filter(Objects::nonNull).toList();

    }

    private static File downloadBlob(BlobContainerClient containerClient, String blobName) {
        BlobClient blobClient = containerClient.getBlobClient(blobName);
        File downloadFile = new File(Paths.get(DOWNLOAD_PATH, blobName).toString());

        // Download the blob to a file
        try (InputStream blobInputStream = blobClient.openInputStream();
             FileOutputStream fileOutputStream = new FileOutputStream(downloadFile)) {

            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = blobInputStream.read(buffer)) != -1) {
                fileOutputStream.write(buffer, 0, bytesRead);
            }

            log.info("Downloaded blob: {} to {}", blobName, downloadFile.getAbsolutePath());
            return downloadFile;
        } catch (Exception e) {
            log.error("Failed to download blob: {}", blobName);
            ProcessingResult.failureResults.add(String.format("Failed to download file %s and exception is %s", downloadFile.getAbsolutePath(), e.getMessage()));
        }
        return null;
    }
}


