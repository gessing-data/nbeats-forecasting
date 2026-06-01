# Desktop Packaging

This directory contains packaging configuration that must stay versioned with the application code.

The Windows build uses Flet's PyInstaller-based `flet pack` command in `onedir` mode. The application depends on NeuralForecast, which imports Ray for its training and tuning infrastructure. Ray performs runtime imports and ships native files that PyInstaller cannot reliably discover from static analysis alone, so custom hooks collect the required Ray and NeuralForecast modules, metadata, data files, and dynamic libraries.

Keep dependency-specific packaging rules here instead of embedding private module names in the GitHub Actions workflow. The workflow should orchestrate the build; this directory should describe how the Python application is packaged.
