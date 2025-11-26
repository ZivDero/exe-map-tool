import dearpygui.dearpygui as dpg

LOCKED_COLOR = (90, 30, 30, 255)

def apply_theme():
    with dpg.theme() as global_theme:
        # CORE style group
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 4, 4)

    dpg.bind_theme(global_theme)

def color_locked_row(row_id):
    dpg.set_item_color(row_id, dpg.mvTableRow_bgColor, LOCKED_COLOR)
