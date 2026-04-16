"""
Tests para cieloapi/filtering.py y cieloapi/correo.py
"""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# cieloapi/filtering.py
# ---------------------------------------------------------------------------

class TestFilterBySearch:

    def test_retorna_todo_sin_query(self):
        from cieloapi.filtering import filter_by_search
        items = [MagicMock(full_name="Juan"), MagicMock(full_name="Pedro")]
        assert filter_by_search(items, "", ["full_name"]) == items

    def test_filtra_por_campo_de_objeto(self):
        from cieloapi.filtering import filter_by_search

        class Obj:
            def __init__(self, name):
                self.full_name = name

        items = [Obj("Juan Perez"), Obj("Pedro Lopez"), Obj("Maria Juan")]
        resultado = filter_by_search(items, "juan", ["full_name"])
        assert len(resultado) == 2

    def test_busqueda_case_insensitive(self):
        from cieloapi.filtering import filter_by_search

        class Obj:
            def __init__(self, name):
                self.full_name = name

        items = [Obj("CARLOS GOMEZ"), Obj("Ana Torres")]
        resultado = filter_by_search(items, "carlos", ["full_name"])
        assert len(resultado) == 1

    def test_sin_resultados(self):
        from cieloapi.filtering import filter_by_search

        class Obj:
            def __init__(self, name):
                self.full_name = name

        items = [Obj("Pedro"), Obj("Maria")]
        assert filter_by_search(items, "zzz", ["full_name"]) == []


class TestFilterBySearchStudents:

    def test_retorna_todo_sin_query(self):
        from cieloapi.filtering import filter_by_search_students
        data = [{"nombre": "Juan"}, {"nombre": "Maria"}]
        assert filter_by_search_students(data, "", ["nombre"]) == data

    def test_filtra_dicts_por_campo(self):
        from cieloapi.filtering import filter_by_search_students
        data = [{"nombre": "Juan Perez"}, {"nombre": "Pedro Lopez"}]
        resultado = filter_by_search_students(data, "juan", ["nombre"])
        assert len(resultado) == 1
        assert resultado[0]["nombre"] == "Juan Perez"

    def test_campo_inexistente_no_rompe(self):
        from cieloapi.filtering import filter_by_search_students
        data = [{"otro": "valor"}]
        resultado = filter_by_search_students(data, "valor", ["nombre"])
        assert resultado == []


class TestGetStatusFilter:

    def test_retorna_true_por_defecto(self):
        from cieloapi.filtering import get_status_filter
        request = MagicMock()
        request.query_params.get.return_value = "false"
        assert get_status_filter(request) is True

    def test_retorna_none_con_show_inactive_true(self):
        from cieloapi.filtering import get_status_filter
        request = MagicMock()
        request.query_params.get.return_value = "true"
        assert get_status_filter(request) is None

    def test_case_insensitive_show_inactive(self):
        from cieloapi.filtering import get_status_filter
        request = MagicMock()
        request.query_params.get.return_value = "True"
        assert get_status_filter(request) is None


# ---------------------------------------------------------------------------
# cieloapi/correo.py
# ---------------------------------------------------------------------------

class TestGetAccessToken:

    @patch("cieloapi.correo.ConfidentialClientApplication")
    def test_retorna_ok_con_token(self, mock_app_cls):
        from cieloapi.correo import get_access_token

        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {"access_token": "tok-abc"}
        mock_app_cls.return_value = mock_app

        with patch.dict("os.environ", {
            "CORREO_CLIENT_ID": "client-id",
            "CORREO_TENANT_ID": "tenant-id",
            "CORREO_SECRET_KEY": "secret",
        }):
            resultado = get_access_token()

        assert resultado["status"] == "OK"
        assert resultado["access"] == "tok-abc"

    @patch("cieloapi.correo.ConfidentialClientApplication")
    def test_retorna_error_sin_access_token(self, mock_app_cls):
        from cieloapi.correo import get_access_token

        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {
            "error_description": "AADSTS70011"
        }
        mock_app_cls.return_value = mock_app

        with patch.dict("os.environ", {
            "CORREO_CLIENT_ID": "id",
            "CORREO_TENANT_ID": "tid",
            "CORREO_SECRET_KEY": "sec",
        }):
            resultado = get_access_token()

        assert resultado["status"] == "ERROR"

    @patch("cieloapi.correo.ConfidentialClientApplication")
    def test_retorna_error_si_falla_construccion_app(self, mock_app_cls):
        from cieloapi.correo import get_access_token

        mock_app_cls.side_effect = Exception("Error de MSAL")

        with patch.dict("os.environ", {
            "CORREO_CLIENT_ID": "id",
            "CORREO_TENANT_ID": "tid",
            "CORREO_SECRET_KEY": "sec",
        }):
            resultado = get_access_token()

        assert resultado["status"] == "ERROR"

    @patch("cieloapi.correo.ConfidentialClientApplication")
    def test_retorna_error_si_falla_acquire_token(self, mock_app_cls):
        from cieloapi.correo import get_access_token

        mock_app = MagicMock()
        mock_app.acquire_token_for_client.side_effect = Exception("Network error")
        mock_app_cls.return_value = mock_app

        with patch.dict("os.environ", {
            "CORREO_CLIENT_ID": "id",
            "CORREO_TENANT_ID": "tid",
            "CORREO_SECRET_KEY": "sec",
        }):
            resultado = get_access_token()

        assert resultado["status"] == "ERROR"


class TestEnviarCorreoMasivo:

    @patch("cieloapi.correo.requests.post")
    @patch("cieloapi.correo.get_template")
    def test_envia_exitosamente(self, mock_tpl, mock_post):
        from cieloapi.correo import enviar_correo_masivo

        mock_tpl.return_value.render.return_value = "<html>correo</html>"
        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_post.return_value = mock_resp

        resultado = enviar_correo_masivo(
            asunto="Test",
            contexto={"key": "val"},
            plantilla="plantilla.html",
            destinatarios=["a@b.com"],
            token="mi-token",
        )
        assert resultado["status"] == "OK"

    @patch("cieloapi.correo.requests.post")
    @patch("cieloapi.correo.get_template")
    def test_retorna_error_en_fallo_http(self, mock_tpl, mock_post):
        from cieloapi.correo import enviar_correo_masivo

        mock_tpl.return_value.render.return_value = "<html>correo</html>"
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_post.return_value = mock_resp

        resultado = enviar_correo_masivo(
            asunto="Test",
            contexto={},
            plantilla="plantilla.html",
            destinatarios=["a@b.com"],
            token="token",
        )
        assert resultado["status"] == "ERROR"

    @patch("cieloapi.correo.requests.post")
    @patch("cieloapi.correo.get_template")
    def test_retorna_error_en_excepcion(self, mock_tpl, mock_post):
        from cieloapi.correo import enviar_correo_masivo

        mock_tpl.side_effect = Exception("Template no encontrado")

        resultado = enviar_correo_masivo(
            asunto="Test",
            contexto={},
            plantilla="no_existe.html",
            destinatarios=["a@b.com"],
            token="token",
        )
        assert resultado["status"] == "ERROR"


class TestEnviarCorreoSimple:

    @patch("cieloapi.correo.requests.post")
    @patch("cieloapi.correo.get_access_token")
    def test_envia_exitosamente(self, mock_token, mock_post):
        from cieloapi.correo import enviar_correo_simple

        mock_token.return_value = {"status": "OK", "access": "tok"}
        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_post.return_value = mock_resp

        resultado = enviar_correo_simple("Asunto", "<p>Hola</p>", ["dest@test.com"])
        assert resultado["status"] == "OK"

    @patch("cieloapi.correo.get_access_token")
    def test_retorna_error_si_token_falla(self, mock_token):
        from cieloapi.correo import enviar_correo_simple

        mock_token.return_value = {"status": "ERROR", "message": "Sin config"}

        resultado = enviar_correo_simple("Asunto", "<p>Hola</p>", ["dest@test.com"])
        assert resultado["status"] == "ERROR"

    @patch("cieloapi.correo.requests.post")
    @patch("cieloapi.correo.get_access_token")
    def test_retorna_error_en_fallo_http(self, mock_token, mock_post):
        from cieloapi.correo import enviar_correo_simple

        mock_token.return_value = {"status": "OK", "access": "tok"}
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"
        mock_post.return_value = mock_resp

        resultado = enviar_correo_simple("Asunto", "<p>Hola</p>", ["dest@test.com"])
        assert resultado["status"] == "ERROR"

    @patch("cieloapi.correo.requests.post")
    @patch("cieloapi.correo.get_access_token")
    def test_retorna_error_en_excepcion(self, mock_token, mock_post):
        from cieloapi.correo import enviar_correo_simple

        mock_token.return_value = {"status": "OK", "access": "tok"}
        mock_post.side_effect = Exception("Timeout")

        resultado = enviar_correo_simple("Asunto", "<p>Hola</p>", ["dest@test.com"])
        assert resultado["status"] == "ERROR"


class TestEnviarCorreoConPlantilla:

    @patch("cieloapi.correo.enviar_correo_masivo")
    @patch("cieloapi.correo.get_access_token")
    def test_delega_a_enviar_masivo(self, mock_token, mock_masivo):
        from cieloapi.correo import enviar_correo_con_plantilla

        mock_token.return_value = {"status": "OK", "access": "tok"}
        mock_masivo.return_value = {"status": "OK", "message": "Enviado"}

        resultado = enviar_correo_con_plantilla(
            asunto="Test",
            plantilla="tpl.html",
            contexto={"k": "v"},
            destinatarios=["a@b.com"],
        )
        assert resultado["status"] == "OK"
        mock_masivo.assert_called_once()

    @patch("cieloapi.correo.get_access_token")
    def test_retorna_error_si_token_falla(self, mock_token):
        from cieloapi.correo import enviar_correo_con_plantilla

        mock_token.return_value = {"status": "ERROR", "message": "Sin credenciales"}

        resultado = enviar_correo_con_plantilla(
            asunto="Test",
            plantilla="tpl.html",
            contexto={},
            destinatarios=["a@b.com"],
        )
        assert resultado["status"] == "ERROR"

    @patch("cieloapi.correo.get_access_token")
    def test_retorna_error_en_excepcion(self, mock_token):
        from cieloapi.correo import enviar_correo_con_plantilla

        mock_token.side_effect = Exception("Error inesperado")

        resultado = enviar_correo_con_plantilla(
            asunto="Test",
            plantilla="tpl.html",
            contexto={},
            destinatarios=["a@b.com"],
        )
        assert resultado["status"] == "ERROR"
