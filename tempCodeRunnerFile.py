def wallet_panel(root):
    """Wallet Panel"""
    w_label = ctk.CTkLabel(
        root,
        text="Wallet",
        text_color="black",
        fg_color="gray"
    )
    w_label.place(x=30, y=450)

    wallet_frame = ctk.CTkFrame(
        root,
        corner_radius=0,
        fg_color="gray",
        width=280,
        height=170
    )
    wallet_frame.place(x=30, y=470)
