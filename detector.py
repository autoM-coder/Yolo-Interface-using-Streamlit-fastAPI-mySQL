import glob
import wget
from PIL import Image
import cv2
import time
import torch


cfg_model_path = 'models/yolov5s.pt'
model = None
confidence = .75


class Detector:
    def __init__(self, st):
        self.st = st

    def image_input(self, data_src):
        img_file = None
        if data_src == 'Sample data':
            # get all sample images
            img_path = glob.glob('data/sample_images/*')
            img_slider = self.st.slider("Select a test image.", min_value=1, max_value=len(img_path), step=1)
            img_file = img_path[img_slider - 1]
        else:
            img_bytes = self.st.sidebar.file_uploader("Upload an image", type=['png', 'jpeg', 'jpg'])
            if img_bytes:
                img_file = "data/uploaded_data/upload." + img_bytes.name.split('.')[-1]
                Image.open(img_bytes).save(img_file)

        if img_file:
            col1, col2 = self.st.columns(2)
            with col1:
                self.st.image(img_file, caption="Selected Image")
            with col2:
                img = self.infer_image(img_file)
                self.st.image(img, caption="Model prediction")

    def video_input(self, data_src):
        vid_file = None
        if data_src == 'Sample data':
            vid_file = "data/sample_videos/video.mp4"
        else:
            vid_bytes = self.st.sidebar.file_uploader("Upload a video", type=['mp4', 'mpv', 'avi'])
            if vid_bytes:
                vid_file = "data/uploaded_data/upload." + vid_bytes.name.split('.')[-1]
                with open(vid_file, 'wb') as out:
                    out.write(vid_bytes.read())

        if vid_file:
            cap = cv2.VideoCapture(vid_file)
            custom_size = self.st.sidebar.checkbox("Custom frame size")
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if custom_size:
                width = self.st.sidebar.number_input("Width", min_value=120, step=20, value=width)
                height = self.st.sidebar.number_input("Height", min_value=120, step=20, value=height)

            fps = 0
            st1, st2, st3 = self.st.columns(3)
            with st1:
                self.st.markdown("## Height")
                st1_text = self.st.markdown(f"{height}")
            with st2:
                self.st.markdown("## Width")
                st2_text = self.st.markdown(f"{width}")
            with st3:
                self.st.markdown("## FPS")
                st3_text = self.st.markdown(f"{fps}")

            self.st.markdown("---")
            output = self.st.empty()
            prev_time = 0
            curr_time = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    self.st.write("Can't read frame, stream ended? Exiting ....")
                    break
                frame = cv2.resize(frame, (width, height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                output_img = self.infer_image(frame)
                output.image(output_img)
                curr_time = time.time()
                fps = 1 / (curr_time - prev_time)
                prev_time = curr_time
                st1_text.markdown(f"**{height}**")
                st2_text.markdown(f"**{width}**")
                st3_text.markdown(f"**{fps:.2f}**")

            cap.release()

    def infer_image(self, img, size=None):
        result = model(img, size=size) if size else model(img)
        result.render()
        image = Image.fromarray(result.ims[0])
        return image

    # @st.cache_resource
    def load_model(self, path, device):
        model_ = torch.hub.load('ultralytics/yolov5', 'custom', path=path, force_reload=True)
        model_.to(device)
        print("model to ", device)
        return model_

    # @st.cache_resource
    def download_model(self, url):
        model_file = wget.download(url, out="models")
        return model_file

    def get_user_model(self):
        model_src = self.st.sidebar.radio("Model source", ["file upload", "url"])
        model_file = None
        if model_src == "file upload":
            model_bytes = self.st.sidebar.file_uploader("Upload a model file", type=['pt'])
            if model_bytes:
                model_file = "models/uploaded_" + model_bytes.name
                with open(model_file, 'wb') as out:
                    out.write(model_bytes.read())
        else:
            url = self.st.sidebar.text_input("model url")
            if url:
                model_file_ = self.download_model(url)
                if model_file_.split(".")[-1] == "pt":
                    model_file = model_file_

        return model_file