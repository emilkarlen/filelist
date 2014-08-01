# -*- awk -*-

# Remove comments and blank lines.
/^ *$/ {
    next;
}

# Copy instruction lines
/^@/ {
    print;
    next;
}

# Append ".txt" to file paths.
{
    print $0 ".txt"
}
