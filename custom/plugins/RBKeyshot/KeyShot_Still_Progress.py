import time
import sys
from pywinauto import Desktop

render_started = False


def get_windows():
    return Desktop(backend="uia").windows()


def is_keyshot_running():

    windows = get_windows()
    keyshot_string = ["KeyShot 9.2 Pro",
                      "KeyShot 9.1 Pro"]
    keyshot_status = False
    for window in windows:
        w_title = window.window_text()
        for version in keyshot_string:
            if version in w_title:
                keyshot_status = True
                return keyshot_status
    return keyshot_status


def is_render_started():

    global render_started
    for window in get_windows():
        w_title = window.window_text()
        if "(Rendering" in w_title:
            print "Render is started : %s " % w_title
            render_started = True
            return


def main(args):
    print args
    global render_started

    def get_progress():
        last_text = str()
        while is_keyshot_running():
            render_window = False
            for window in get_windows():
                text = window.window_text()
                if "(Rendering " in text:
                    render_window = True
                    if text != last_text:
                        last_text = text
                        sys.stdout.write(str(text) + "\n")
                        print text
                    time.sleep(2)
            if not render_window:
                print "Render window is closed."
                sys.exit()

    # wait for 10 second to start render
    for i in range(10):
        if not render_started:
            is_render_started()
            time.sleep(2)
            print "Waiting for render window ..."

    get_progress()


if __name__ == '__main__':
    main(sys.argv[1:])
