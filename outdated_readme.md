<strike>  0. Prerequisites: One of the following Python versions installed on your system: 3.{7,8,9,10,11,12}. 

1. Clone the repository (or download it as .zip from this page) and navigate into the folder:
```bash
git clone https://github.com/evermoving/SystemCaptioner
cd SystemCaptioner
```
2. Create a virtual environment inside the cloned repo: 
```bash
python -m venv venv
```
3. Activate the virtual environment:
```bash
.\venv\Scripts\activate
```
4. Install the dependencies:
```bash
pip install -r requirements.txt
```
5. Download nvidia_dependencies zip from the releases section and extract it into folder where main.py is, i.e. `/SystemCaptioner/nvidia_dependencies/`
6. Launch main.py while in virtual environment:
```bash
python main.py