package ai.scaia.tika;
/*
 *@created 04/06/2024- 15:13
 *@author neha
 */

import ai.scaia.config.Config;
import ai.scaia.result.ProcessingResult;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Paths;

import static java.util.concurrent.TimeUnit.SECONDS;

@Slf4j
public class TikaFileProcessor {

    private static final MediaType MEDIA_TYPE_BINARY = MediaType.parse("application/octet-stream");
    private static final String EXTRACTED_TEXT_PATH = "/tmp/";

    private static final OkHttpClient restClient = new OkHttpClient.Builder()
            .connectTimeout(10, SECONDS)
            .readTimeout(300, SECONDS)
            .writeTimeout(300, SECONDS)
            .build();

    public static String getText(File file) throws Exception {
        String output = "";
        String ocrHeaderName = "X-Tika-PDFOcrStrategy";
        String ocrHeaderValue = "ocr_and_text_extraction";

        log.info("Sending PUT request to Tika server with URL {}: ", Config.getProperty("tika.url"));
        log.info("File: {}", file.getAbsolutePath());

        Request request = new Request.Builder()
                .url(Config.getProperty("tika.url"))
                .addHeader("Accept", "text/plain")
                .addHeader(ocrHeaderName, ocrHeaderValue)
                .put(RequestBody.create(MEDIA_TYPE_BINARY, file))
                .build();

        try (Response response = restClient.newCall(request).execute()) {
            log.info("Response Code: {}, Message {}", response.code(), response.message());

            if (!response.isSuccessful()) {
                throw new IOException("Unexpected code " + response);
            }
            if (response.body() != null) {
                output = response.body().string();
            }
        } catch (IOException ex) {
            log.error("failed to extract text from file: {} with exception {}", file, ex.getMessage());
            ProcessingResult.failureResults.add(String.format("failed to extract text from file:%s with exception %s", file, ex.getMessage()));
        }

        return output;
    }

    public static void saveExtractedText(String fileName, String extractedText) {
        String textFileName = fileName + ".json";
        File textFile = new File(Paths.get(EXTRACTED_TEXT_PATH, textFileName).toString());
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(textFile))) {
            writer.write(extractedText);
            log.info("Saved extracted text to: {}", textFile.getAbsolutePath());
        } catch (IOException e) {
            log.error("Failed to save extracted text: {}", textFileName);
            ProcessingResult.failureResults.add("failed to save extracted text for: %s " + textFileName);
        }
    }
}
