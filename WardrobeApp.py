import streamlit as st
import sqlite3
import os
from openai import OpenAI
import time
import base64
import streamlit.components.v1 as components

current_dir = os.path.dirname(os.path.abspath(__file__))
timer_path = os.path.join(current_dir, "camera_addon")
auto_camera = components.declare_component("cam_final_check", path=timer_path)


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="My Virtual Wardrobe", page_icon="👗", layout="centered")

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'welcome'
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'model_image_path' not in st.session_state:
    st.session_state.model_image_path = None
if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'global_canvas' not in st.session_state:
    st.session_state.global_canvas = st.session_state.get('model_image_path', None)


def switch_page(page_name):
    st.session_state.current_page = page_name


def logout():
    st.session_state.logged_in_user = None
    st.session_state.model_image_path = None
    switch_page('welcome')


def init_db():
    conn = sqlite3.connect('my_users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (username TEXT PRIMARY KEY, email TEXT, password TEXT, model_image_path TEXT)''')
    conn.commit()
    conn.close()


def profile_sidebar():
    if st.session_state.logged_in_user:
        with st.sidebar:
            st.header(f"Hello, {st.session_state.logged_in_user}! 👋")
            st.markdown("---")

            if st.session_state.model_image_path:
                st.image(st.session_state.model_image_path, caption="Your Profile Picture", use_container_width=True)

            st.markdown("---")

            st.button("Instructions", on_click=switch_page, args=('instructions',), use_container_width=True)
            st.button("Change your permanent model", on_click=switch_page, args=('change model',),
                      use_container_width=True)
            st.button("Log Out", on_click=logout, use_container_width=True)


###### welcome page - before login/signup
def welcome_page():
    st.title("Welcome to your Virtual Wardrobe!")
    st.markdown("Please login / signup to continue")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Log In", on_click=switch_page, args=('login',), use_container_width=True)
    with col2:
        st.button("Sign Up", on_click=switch_page, args=('register',), use_container_width=True)


#####login page
def login_page():
    # elif st.session_state.current_page == 'login':
    st.title("Log In")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Submit Login"):
            conn = sqlite3.connect('my_users.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                st.session_state.logged_in_user = username
                st.session_state.model_image_path = user[3]
                st.success("Logged in successfully!")
                switch_page('instructions')
                st.rerun()
            else:
                st.error("Wrong username and/or password")
    st.button("BACK", on_click=switch_page, args=('welcome',))


####signup page
def signup_page():
    st.title("Sign Up")
    with st.form("register_form"):
        username = st.text_input("Choose a Username")
        email = st.text_input("Email")
        password = st.text_input("Choose a Password", type="password")
        uploaded_file = st.file_uploader("Upload your default Model Image", type=["jpg", "jpeg", "png"])

        if st.form_submit_button("Create Account"):
            if not username or not email or not password or uploaded_file is None:
                st.error("Please fill out all fields and upload an image.")
            else:
                try:
                    if not os.path.exists("user_models"): os.makedirs("user_models")
                    ext = os.path.splitext(uploaded_file.name)[1]
                    saved_image_path = os.path.join("user_models", f"{username}_model{ext}")
                    with open(saved_image_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    conn = sqlite3.connect('my_users.db')
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                                   (username, email, password, saved_image_path))
                    conn.commit()
                    conn.close()

                    st.session_state.logged_in_user = username
                    st.session_state.model_image_path = saved_image_path
                    st.success("Account created successfully!")
                    # שינוי: מעביר ישירות לעמוד ההוראות!
                    switch_page('instructions')
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already taken... try again")
    st.button("🔙 Back to Welcome", on_click=switch_page, args=('welcome',))


####instructions page
def instructions_page():
    st.title("How to use your Virtual Wardrobe?")

    st.markdown("""
        Welcome to your personal virtual dressing room! Here is what you can do:

        * **🎨 Color Changer:** Upload an image and change the color of your clothes using. You can change the color of multiple items at the same time!
        * **✨ Virtual Try-On:** Upload a picture of a clothing item and see how it looks on you! You can try on multiple items at the same time!
        * **🖌️ Custom Design:** Choose one item and describe what print/design you would like it to have. Make sure to not ask for something overly complicated and describe BOTH the background and the print for best results...
        * **💻 AI Consult:** Upload up to 3 pictures and ask our AI stylist for some fashion advice! Make sure your request is clear and understandable.

        * **Important note:** Make sure your model picture is in good quality with a clear background for the best results. 
        * **Another important note:** Even tho you can use the same picture you've already modified multiple times please press "CLEAR" every few uses for best results. 


        Choose what you want to do next:
        """)

    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        st.button("Go to Color Changer 🎨 ", on_click=switch_page, args=('changecolor',), use_container_width=True)
        st.button("Make Your Own Design 🖌️ ", on_click=switch_page, args=('custom design',), use_container_width=True)
    with col2:
        st.button("Go to Virtual Try-On ✨ ", on_click=switch_page, args=('tryon',), use_container_width=True)
        st.button("Consult With AI 💻 ", on_click=switch_page, args=('consult page',), use_container_width=True)


##### Recolor your clothes page
def changecolor_page():
    st.title("Recolor your outfit! 🎨 ")
    st.button("BACK", on_click=switch_page, args=('instructions',))
    st.markdown("---")

    if 'global_canvas' not in st.session_state or not st.session_state.global_canvas:
        st.session_state.global_canvas = st.session_state.model_image_path

    if 'mixer_colors' not in st.session_state:
        st.session_state.mixer_colors = {
            "Top": "Original", "Bottom": "Original", "Dress": "Original", "Jacket": "Original", "Shoes": "Original",
            "Glasses": "Original"
        }

    if 'last_result' not in st.session_state:
        st.session_state.last_result = None

    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        st.markdown("<h4 style='text-align: center; color: #b764d4;'>Customize Your Colors</h4>",
                    unsafe_allow_html=True)

        color_options = ["Original", "Red", "Blue", "Green", "Black", "White", "Pink", "Yellow", "Purple", "Beige"]

        for item in st.session_state.mixer_colors.keys():
            col_sel, col_reset = st.columns([4, 1])
            with col_sel:
                st.session_state.mixer_colors[item] = st.selectbox(
                    f"{item} Color:", color_options,
                    index=color_options.index(st.session_state.mixer_colors[item]),
                    key=f"select_{item}"
                )

        st.markdown("---")

        if st.button("Use Permanent Model 👤", use_container_width=True):
            st.session_state.global_canvas = st.session_state.model_image_path
            st.session_state.last_result = None
            st.rerun()

        with st.popover("Take Live Photo 📸", use_container_width=True):
            image_b64 = auto_camera(key="camera_new_v1")

            if 'last_captured_image_color' not in st.session_state:
                st.session_state.last_captured_image_color = None

            if image_b64 and image_b64 != st.session_state.last_captured_image_color:

                st.session_state.last_captured_image_color = image_b64

                header, encoded = image_b64.split(",", 1)
                image_bytes = base64.b64decode(encoded)

                if not os.path.exists("user_models"):
                    os.makedirs("user_models")

                temp_model_path = os.path.join("user_models",
                                               f"live_model_{st.session_state.logged_in_user}.png")

                with open(temp_model_path, "wb") as f:
                    f.write(image_bytes)

                st.session_state.global_canvas = temp_model_path

                st.rerun()

        st.write("")

        if st.button("🪄 UPDATE COLORS", type="primary", use_container_width=True):
            active_changes = [f"{k} to {v}" for k, v in st.session_state.mixer_colors.items() if v != "Original"]

            if not active_changes:
                st.error("Please select at least one color to change!")
            elif 'client' not in globals() or client is None:
                st.error("API Key missing.")
            else:
                changes_str = ", ".join(active_changes)
                with st.spinner(f"Changing {changes_str}... ✨"):
                    try:
                        image_to_edit = st.session_state.last_result if st.session_state.last_result else st.session_state.global_canvas
                        file_to_send = open(image_to_edit, "rb")
                        prompt = f"""
                        Change the colors of these items: {changes_str}.
                        Rules:
                        - If an item is not present in the image, do NOT change anything else.
                        - Do NOT change the persons face, pose, and body, or the background.
                        - Maintain the original texture and fabric fold.
                        - If you get a request to change the color of an item that is not present in the picture, DO NOT CHANGE ANYTHING and move on to the next item.
                        - If you need to change the color of glasses/sunglasses change ONLY the color of the frames.
                        """
                        result = client.images.edit(
                            model="gpt-image-1",
                            image=[file_to_send],
                            prompt=prompt,
                            input_fidelity="high"
                        )
                        file_to_send.close()

                        image_bytes = base64.b64decode(result.data[0].b64_json)
                        res_path = os.path.join("user_models", f"color_res_{st.session_state.logged_in_user}.png")
                        with open(res_path, "wb") as f:
                            f.write(image_bytes)

                        st.session_state.last_result = res_path
                        st.success("Done! 🎉")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col_right:

        st.subheader("Your Model 👤✨")

        if st.session_state.last_result:
            st.image(st.session_state.last_result, use_container_width=True)

        else:
            if st.session_state.global_canvas:
                st.image(st.session_state.global_canvas, use_container_width=True)

        if st.button("Clear All 🔄", use_container_width=True):
            for item in st.session_state.mixer_colors:
                st.session_state.mixer_colors[item] = "Original"
            st.session_state.global_canvas = st.session_state.model_image_path
            st.session_state.last_result = None
            st.rerun()


##### tryon page
def tryon_page():
    st.title("Change your outfit! 🎨 ")
    st.button("BACK", on_click=switch_page, args=('instructions',))
    st.markdown("---")

    if 'global_canvas' not in st.session_state or not st.session_state.global_canvas:
        st.session_state.global_canvas = st.session_state.model_image_path

    if 'last_result' not in st.session_state:
        st.session_state.last_result = None

    if 'clothing_items' not in st.session_state:
        st.session_state.clothing_items = {
            "top": None, "bottom": None, "dress": None, "jacket": None, "shoes": None, "glasses": None
        }

    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        st.markdown("<h4 style='text-align: center; color: #b764d4;'>Please choose clothes and model</h4>",
                    unsafe_allow_html=True)
        st.write("")

        categories = {
            "top": "Add Top 👕",
            "bottom": "Add Bottom 👖",
            "dress": "Add Dress 👗",
            "jacket": "Add Jacket 🧥",
            "shoes": "Add Shoes 👟",
            "glasses": "Add Glasses 🕶️"
        }

        for cat_key, btn_text in categories.items():
            with st.popover(btn_text, use_container_width=True):
                input_method = st.radio(f"How to add?", ["Upload Image", "Use Camera"], horizontal=True,
                                        key=f"radio_{cat_key}")

                uploaded_item = None
                if input_method == "Upload Image":
                    uploaded_item = st.file_uploader("Upload File", type=["png", "jpg", "jpeg", "webp", "jfif"],
                                                     key=f"up_{cat_key}", label_visibility="collapsed")
                else:
                    uploaded_item = st.camera_input("Take a picture", key=f"cam_{cat_key}")

                if st.button(f"Save to {cat_key.capitalize()}", key=f"save_{cat_key}", use_container_width=True):
                    if uploaded_item:
                        if not os.path.exists("user_models"): os.makedirs("user_models")
                        file_path = os.path.join("user_models", f"temp_{st.session_state.logged_in_user}_{cat_key}.png")
                        with open(file_path, "wb") as f:
                            f.write(uploaded_item.getbuffer())
                        st.session_state.clothing_items[cat_key] = file_path
                        st.rerun()

        st.markdown("---")

        if st.button("Use Permanent Model 👤", use_container_width=True):
            st.session_state.global_canvas = st.session_state.model_image_path
            st.session_state.last_result = None
            st.rerun()

        with st.popover("Take Live Photo 📸", use_container_width=True):
            image_b64 = auto_camera(key="camera_new_v1")

            if 'last_captured_image' not in st.session_state:
                st.session_state.last_captured_image = None

            if image_b64 and image_b64 != st.session_state.last_captured_image:

                st.session_state.last_captured_image = image_b64

                header, encoded = image_b64.split(",", 1)
                image_bytes = base64.b64decode(encoded)

                if not os.path.exists("user_models"):
                    os.makedirs("user_models")

                temp_model_path = os.path.join("user_models",
                                               f"live_model_{st.session_state.logged_in_user}.png")

                with open(temp_model_path, "wb") as f:
                    f.write(image_bytes)

                st.session_state.global_canvas = temp_model_path
                st.session_state.last_result = None

                st.rerun()

        st.write("")

        if st.button("✨ TRY ON ✨", use_container_width=True, type="primary"):
            active_items = {k: v for k, v in st.session_state.clothing_items.items() if v is not None}
            if not active_items:
                st.error("Please add at least one clothing item!")
            elif 'client' not in globals() or client is None:
                st.error("OpenAI API Key is missing.")
            else:
                items_str = ", ".join(active_items.keys())
                with st.spinner(f"Creating magic with {items_str}... ✨ Please wait."):
                    try:
                        base_image = st.session_state.last_result if st.session_state.last_result else st.session_state.global_canvas
                        files_to_send = [open(base_image, "rb")]
                        for path in active_items.values():
                            files_to_send.append(open(path, "rb"))

                        prompt = f"""
                            Take the person in the first image and dress them with the items provided in the subsequent images: {items_str}.
                            - Maintain the exact texture, color, and design of each clothing item.
                            - If the item the model is already wearing has a logo/drawing on it and that is the item you need to replace with a new one, make sure to not leave the logo on the new item you fit on the model.   
                            - Ensure all items ({items_str}) are layered naturally on the body at the same time.
                            - Do not modify the person's face, pose, or the background.
                            - The output should be a single image of the person wearing all selected items.
                            """

                        result = client.images.edit(
                            model="gpt-image-1",
                            image=files_to_send,
                            prompt=prompt,
                            input_fidelity="high"
                        )

                        for f in files_to_send:
                            f.close()

                        image_bytes = base64.b64decode(result.data[0].b64_json)
                        final_path = os.path.join("user_models", f"final_tryon_{st.session_state.logged_in_user}.png")

                        with open(final_path, "wb") as f:
                            f.write(image_bytes)

                        st.session_state.last_result = final_path
                        st.success("Done! ✨")
                        st.rerun()

                    except Exception as e:
                        st.error(f"API Error details: {e}")

    with col_right:
        st.subheader("Your Model 👤✨")
        if st.session_state.last_result:
            st.image(st.session_state.last_result, use_container_width=True)
        else:
            st.image(st.session_state.global_canvas, use_container_width=True)

        st.markdown("---")

        st.markdown("**👗 Current Selected Items:**")
        outfit_cols = st.columns(6)
        for i, (cat, path) in enumerate(st.session_state.clothing_items.items()):
            with outfit_cols[i]:
                if path and os.path.exists(path):
                    st.image(path, use_container_width=True)
                    st.caption(cat.capitalize())
                    if st.button("❌", key=f"del_{cat}", use_container_width=True):
                        st.session_state.clothing_items[cat] = None
                        st.rerun()

        st.write("")

        if st.button("Clear All 🔄", use_container_width=True):
            st.session_state.global_canvas = st.session_state.model_image_path
            st.session_state.last_result = st.session_state.model_image_path
            st.session_state.clothing_items = {
                "top": None, "bottom": None, "dress": None, "jacket": None, "shoes": None, "glasses": None
            }
            st.rerun()

#### change the permanent model page
def changemodel_page():
    st.title("Change Your Permanent Model 👤")
    st.markdown("Update your base photo. This photo will be used for all Try-On and Color changes.")

    st.button("BACK", on_click=switch_page, args=('instructions',))
    st.write("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Current Model")
        if st.session_state.model_image_path and os.path.exists(st.session_state.model_image_path):
            st.image(st.session_state.model_image_path, caption="Your active photo", use_container_width=True)
        else:
            st.info("No model uploaded yet.")

    with col2:
        st.subheader("Upload New Photo")
        upload_method = st.radio("Choose source:", ["Upload from PC", "Take a Live Photo"], horizontal=True)

        new_img = None
        if upload_method == "Upload from PC":
            new_img = st.file_uploader("Choose an image file", type=["png", "jpg", "jpeg", "webp", "jfif"])
        else:
            new_img = st.camera_input("Snap a new profile photo")

        if st.button("Update Permanent Model ✅ ", type="primary", use_container_width=True):
            if new_img:
                with st.spinner("Updating your profile..."):
                    if not os.path.exists("user_models"):
                        os.makedirs("user_models")

                    new_path = os.path.join("user_models", f"perm_model_{st.session_state.logged_in_user}.png")

                    with open(new_path, "wb") as f:
                        f.write(new_img.getbuffer())

                    st.session_state.model_image_path = new_path
                    st.session_state.global_canvas = new_path

                    conn = sqlite3.connect('my_users.db')
                    cursor = conn.cursor()
                    cursor.execute("""
                                            UPDATE users 
                                            SET model_image_path = ? 
                                            WHERE username = ?
                                        """, (new_path, st.session_state.logged_in_user))
                    conn.commit()
                    conn.close()

                    st.success("Success! Your permanent model has been updated.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Please select or take a photo first!")

    st.write("---")
    st.info("💡 Note: Changing your permanent model will reset any current outfit or color changes you've made.")

##### make a custom print page
def customdesign_page():
    st.title("Desgin Your Own Print!")
    st.button("BACK", on_click=switch_page, args=('instructions',))
    st.markdown("---")

    if 'global_canvas' not in st.session_state or not st.session_state.global_canvas:
        st.session_state.global_canvas = st.session_state.model_image_path

    if 'last_result' not in st.session_state:
        st.session_state.last_result = None

    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        st.markdown("<h4 style='text-align: center; color: #b764d4;'>Design Your Clothes</h4>", unsafe_allow_html=True)

        item_to_change_desgin = st.selectbox(
            "1. Which item do you want to redesign?",
            ["Top ", "Bottom ", "Dress", "Jacket ", "Shoes", "Glasses"]
        )

        design_prompt = st.text_area(
            "2. Describe your dream design:",
            placeholder="Example: A white background with green polka dots..."
        )

        st.markdown("---")

        if st.button("Use Permanent Model 👤", use_container_width=True):
            st.session_state.global_canvas = st.session_state.model_image_path
            st.session_state.last_result = None
            st.rerun()

        with st.popover("Take Live Photo 📸", use_container_width=True):
            image_b64 = auto_camera(key="camera_new_v1")

            if 'last_captured_image_design' not in st.session_state:
                st.session_state.last_captured_image_design = None

            if image_b64 and image_b64 != st.session_state.last_captured_image_design:

                st.session_state.last_captured_image_design = image_b64

                header, encoded = image_b64.split(",", 1)
                image_bytes = base64.b64decode(encoded)

                if not os.path.exists("user_models"):
                    os.makedirs("user_models")

                temp_model_path = os.path.join("user_models",
                                               f"live_model_{st.session_state.logged_in_user}.png")

                with open(temp_model_path, "wb") as f:
                    f.write(image_bytes)

                st.session_state.global_canvas = temp_model_path
                st.rerun()

        st.write("")

        if st.button("🪄 GENERATE DESIGN", type="primary", use_container_width=True):
            if not design_prompt:
                st.error("Please describe your design first!")
            elif 'client' not in globals() or client is None:
                st.error("OpenAI API Key missing.")
            else:
                with st.spinner(f"Designing your {item_to_change_desgin}... ✨"):
                    try:
                        image_to_send = st.session_state.last_result if st.session_state.last_result else st.session_state.global_canvas
                        file = open(image_to_send, "rb")
                        prompt = f"""
                        Take the person in the image and redesign their {item_to_change_desgin}.
                        New design description: {design_prompt}.
                        IMPORTANT RULES:
                        - Keep the exact original shape and folds of the clothing.
                        - Do not modify the person's face, body, pose, or the background.
                        - Only change the pattern and color of the specified {item_to_change_desgin}.
                        - If you receive a request to change the design of a none existing item, do not change anything and ignore the request.
                        """
                        result = client.images.edit(
                            model="gpt-image-1",
                            image=[file],
                            prompt=prompt,
                            input_fidelity="high"
                        )
                        file.close()

                        image_bytes = base64.b64decode(result.data[0].b64_json)
                        result_path = os.path.join("user_models", f"custom_res_{st.session_state.logged_in_user}.png")
                        with open(result_path, "wb") as f:
                            f.write(image_bytes)

                        st.session_state.global_canvas = result_path
                        st.session_state.last_result = result_path
                        st.success("Done! 🎉")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col_right:

        st.subheader("Your Model 👤✨")

        if st.session_state.last_result:
            st.image(st.session_state.last_result, use_container_width=True)
        else:
            st.image(st.session_state.global_canvas, use_container_width=True)

        if st.button("Clear 🔄 ", use_container_width=True):
            st.session_state.global_canvas = st.session_state.model_image_path
            st.session_state.last_result = None
            st.rerun()

#### פונקציית עזר
def encode_image_for_api(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

#####get advice from AI
def consult_page():
    st.title("Consult with AI!")
    st.button("BACK", on_click=switch_page, args=('instructions',))
    st.markdown("---")

    st.markdown("#### Upload up to 3 items and ask for styling advice!")

    uploaded_files = st.file_uploader(
        "Choose your items (Top, Bottoms, Shoes...)",
        type=["png", "jpg", "jpeg", "jfif", "webp"],
        accept_multiple_files=True
    )

    if len(uploaded_files) > 3:
        st.warning("Please upload a maximum of 3 images. We'll only use the first 3.")
        uploaded_files = uploaded_files[:3]

    if uploaded_files:
        cols = st.columns(len(uploaded_files))
        for i, file in enumerate(uploaded_files):
            with cols[i]:
                st.image(file, use_container_width=True)

    st.markdown("---")

    user_question = st.text_area(
        "What's your styling dilemma?",
        placeholder="Example: Which of these two pants looks better with the white shirt?"
    )

    if st.button("Ask AI 🪄", type="primary", use_container_width=True):
        if not uploaded_files:
            st.error("Please upload at least one image to get advice!")
        elif not user_question:
            st.error("Please ask a styling question!")
        elif 'client' not in globals() or client is None:
            st.error("OpenAI API Key missing.")
        else:
            with st.spinner("Analyzing your question & pictures... ✨"):
                try:
                    content_list = [{"type": "text", "text": user_question}]

                    for file in uploaded_files:
                        base64_image = encode_image_for_api(file)
                        content_list.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        })

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a professional, trendy, and highly helpful personal fashion stylist. Give practical styling advice based on the images and question provided. Explain why certain items work well together. If you get an inappropriate image or an inappropriate/unreadable question return the following sentence: Sorry, I am unable to answer your question, please try again with a different question/image."
                            },
                            {
                                "role": "user",
                                "content": content_list
                            }
                        ],
                        max_tokens=800
                    )

                    ai_response = response.choices[0].message.content

                    st.success("Got it! Here is your advice:")
                    st.info(ai_response)

                except Exception as e:
                    st.error(f"Error: {e}")


def main():
    init_db()
    profile_sidebar()

    if st.session_state.current_page == 'welcome':
        welcome_page()
    elif st.session_state.current_page == 'login':
        login_page()
    elif st.session_state.current_page == 'register':
        signup_page()
    elif st.session_state.current_page == 'instructions':
        instructions_page()
    elif st.session_state.current_page == 'changecolor':
        changecolor_page()
    elif st.session_state.current_page == 'tryon':
        tryon_page()
    elif st.session_state.current_page == 'change model':
        changemodel_page()
    elif st.session_state.current_page == 'custom design':
        customdesign_page()
    elif st.session_state.current_page == 'consult page':
        consult_page()





if __name__ == "__main__":
    main()