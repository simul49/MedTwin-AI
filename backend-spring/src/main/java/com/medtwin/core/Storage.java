package com.medtwin.core;

import com.medtwin.config.AppProps;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;

/** Resolves the shared document store used by both the old Django code and Spring. */
@Service
public class Storage {
    private final Path root;

    public Storage(AppProps props) {
        Path cwd = Path.of("").toAbsolutePath().normalize();
        Path configured = cwd.resolve(props.getUploadDir()).normalize();
        Path sibling = cwd.resolve("../backend/var/documents").normalize();
        Path child = cwd.resolve("backend/var/documents").normalize();
        if (Files.isDirectory(configured)) root = configured;
        else if (Files.isDirectory(sibling)) root = sibling;
        else if (Files.isDirectory(child)) root = child;
        else root = configured;
    }

    public Path root() {
        return root;
    }

    public Path resolve(String relative) {
        Path target = root.resolve(relative).normalize();
        if (!target.startsWith(root)) throw ApiError.bad("Invalid file path.");
        return target;
    }
}
