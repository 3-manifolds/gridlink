import gridlink

def main():
    App = gridlink.GridlinkApp()
    try:
        App.root.tk.call('console','hide')
    except:
        pass
    App.root.focus()
    App.root.mainloop()
    
if __name__ == '__main__':
    main()
