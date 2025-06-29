import logging
import sys

def setup_logger(
    logger_name: str = None,
    level: int = logging.INFO,
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    date_format: str = '%Y-%m-%d %H:%M:%S',
    log_to_console: bool = True,
    log_file: str = None
) -> logging.Logger:
    """
    Set up a logger with specified configurations.

    Args:
        logger_name: Name of the logger. If None, returns the root logger.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_format: Format string for log messages.
        date_format: Format string for the date/time in log messages.
        log_to_console: If True, logs to the console (stdout).
        log_file: Optional path to a file where logs should be written.

    Returns:
        Configured Logger object.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Prevent multiple handlers if logger is already configured
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(log_format, datefmt=date_format)

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except IOError as e:
            # Fallback to console if file logging fails
            print(f"Error setting up file handler for {log_file}: {e}. Logging to console only.")
            if not log_to_console: # If console logging wasn't initially requested
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)


    # Set propagation to False if it's not the root logger to avoid duplicate root logs
    if logger_name:
        logger.propagate = False

    return logger

if __name__ == '__main__':
    # Example Usage

    # 1. Get the root logger with default settings
    root_logger = setup_logger(level=logging.DEBUG)
    root_logger.debug("This is a debug message from root logger.")
    root_logger.info("This is an info message from root logger.")

    # 2. Get a custom logger
    custom_logger = setup_logger("MyModuleLogger", level=logging.INFO)
    custom_logger.info("This is an info message from MyModuleLogger.")
    custom_logger.warning("This is a warning from MyModuleLogger.")

    # 3. Custom logger with file output
    file_logger = setup_logger(
        "FileLogger",
        level=logging.DEBUG,
        log_file="app.log",
        log_format='%(levelname)-8s %(asctime)s %(name)s: %(message)s'
    )
    file_logger.debug("This message goes to app.log (and console).")
    file_logger.info("Another message for app.log (and console).")
    file_logger.error("An error message for app.log (and console).")

    print("\\nLog messages should have been printed to console and 'app.log'.")
    print("Check 'app.log' for file output.")

    # 4. Test logger without console output (only to file)
    file_only_logger = setup_logger("FileOnlyLogger", log_to_console=False, log_file="file_only.log")
    if file_only_logger.hasHandlers(): # Check if handlers were successfully added
        file_only_logger.info("This message should only be in file_only.log.")
        print("Message sent to file_only.log (not console).")
    else:
        print("FileOnlyLogger has no handlers, something went wrong.")


    # 5. Test logger name propagation (should not duplicate to root if propagate=False)
    # First, ensure root logger has a handler (it does from setup_logger call above)
    # Then, create a child logger. Messages to child should not appear from root.
    child_logger = setup_logger("MyModuleLogger.Child", level=logging.DEBUG) # MyModuleLogger is parent
    child_logger.debug("Debug message from child logger - should not be duplicated by root.")


    # Example of how a library might use the root logger if not careful
    # This shows why logger.propagate = False is often useful for named loggers
    # To test this, temporarily set propagate=True for custom_logger:
    # custom_logger.propagate = True
    # custom_logger.info("This info from custom_logger might now also appear from root if propagate is True.")
    # custom_logger.propagate = False # Reset

    print("\\nLogger configuration tests finished.")
