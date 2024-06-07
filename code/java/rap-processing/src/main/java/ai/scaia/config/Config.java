package ai.scaia.config;/*
 *@created 04/06/2024- 17:53
 *@author neha
 */

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.Properties;

public class Config {

    private static final String USER_HOME_PROPERTY_FILE = System.getProperty("user.home") + "/config.properties";
    private static final String RESOURCE_PROPERTY_FILE = "config.properties";

    private static final Properties properties = new Properties();

    static {
        try (InputStream input = getPropertyFileInputStream()) {
            if (input == null) {
                throw new RuntimeException("Unable to find config.properties");
            }
            properties.load(input);
        } catch (Exception ex) {
            throw new RuntimeException("Could not load config.properties", ex);
        }
    }

    private static InputStream getPropertyFileInputStream() throws IOException {
        // Check if the property file exists in the user's home directory
        if (Files.exists(Paths.get(USER_HOME_PROPERTY_FILE))) {
            return new FileInputStream(USER_HOME_PROPERTY_FILE);
        }

        // If not found, load the property file from the resources
        InputStream resourceStream = Config.class.getClassLoader().getResourceAsStream(RESOURCE_PROPERTY_FILE);
        if (resourceStream != null) {
            return resourceStream;
        }

        return null; // If neither location has the file, return null
    }

    public static String getProperty(String key) {
        return properties.getProperty(key);
    }

    public static List<String> getQuestionsFromProperties() {
        return properties.stringPropertyNames().stream().filter( k-> k.startsWith("question")).map(properties::getProperty).toList();
    }
}

