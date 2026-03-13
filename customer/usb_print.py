import win32print

def print_label_usb(zpl_text):
    printer_name = "ZDesigner ZD220-203dpi ZPL"  #Exact name of the printer from control panel   
    hPrinter = win32print.OpenPrinter(printer_name)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("Zebra_Label", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, zpl_text.encode('utf-8'))
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)
