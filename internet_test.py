# filename: internet_test.py

import speedtest
import subprocess

def test_internet_speed():
    st = speedtest.Speedtest()

    # Realiza a medição de download
    download_speed = st.download()

    # Realiza a medição de upload
    upload_speed = st.upload()

    # Imprime as velocidades de download e upload
    print(f"Velocidade de Download: {download_speed} Mbps")
    print(f"Velocidade de Upload: {upload_speed} Mbps")

def test_ping(url):
    try:
        response = subprocess.check_output(["ping", "-c", "4", url], stderr=subprocess.STDOUT, text=True)
        print(response)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao testar o ping: {e.output}")

if __name__ == "__main__":
    url = input("Digite a URL do site para testar a conexão: ")
    test_internet_speed()
    print("\n")
    test_ping(url)
