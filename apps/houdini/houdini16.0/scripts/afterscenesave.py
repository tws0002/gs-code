# executed after a scenefile is saved

# afterscenesave.py
import subprocess

### Only run the command if the save succeeded and it's
### not an autosave
##if kwargs["success"] and not kwargs["autosave"]:
##    # Pass the scene file path to the git command
##    subprocess.call("git", "add", kwargs["file"])

def main():
    return

if __name__ == '__main__':
  main()