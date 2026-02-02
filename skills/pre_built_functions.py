import os
import logging
import tempfile
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

# Exception local
class RepoReadError(Exception):
    """Erro ao ler repositório."""
    pass

async def read_repo_context(repo_url: str, branch: str) -> str:
    """
    Clona um repositório (público ou privado) em um diretório temporário,
    executa `npx repomix --stdout` e retorna o resultado como string.
    
    Requer variáveis de ambiente:
    - REPO_PROVIDER: provider do repositório (ex: github.com)
    - REPO_USERNAME: usuário para autenticação
    - REPO_TOKEN: token para autenticação
    """
    provider = os.getenv("REPO_PROVIDER")
    username = os.getenv("REPO_USERNAME")
    token = os.getenv("REPO_TOKEN")

    repo_url = repo_url.removesuffix(".git")
    base_repo = repo_url.removeprefix("https://").removeprefix("http://")
    
    if not (username and token and provider):
        raise RepoReadError("Variáveis REPO_PROVIDER, REPO_USERNAME e REPO_TOKEN são obrigatórias.")

    if provider not in base_repo:
        raise RepoReadError(f"URL do repositório '{repo_url}' não pertence ao provedor '{provider}'")

    source_repo_url = f"https://{username}:{token}@{base_repo}.git"
    
    try:
        logger.debug(f"Iniciando leitura do repositório '{repo_url}' na branch '{branch}'")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            logger.debug(f"Clonando para diretório temporário: {tmp_path}")

            clone_cmd = ["git", "clone", "-b", branch, source_repo_url, str(tmp_path)]
            clone_proc = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            clone_output = []
            async for line in clone_proc.stdout:
                line = line.decode().strip()
                if line:
                    logger.debug(f"[git] {line}")
                    clone_output.append(line)

            await clone_proc.wait()

            if clone_proc.returncode != 0:
                error_msg = f"Falha ao clonar o repositório '{repo_url}'. Saída: {clone_output[-5:]}"
                raise RepoReadError(error_msg)

            logger.debug("Clone concluído com sucesso.")

            repomix_cmd = ["npx", "-y", "repomix", "--stdout"]
            repomix_proc = await asyncio.create_subprocess_exec(
                *repomix_cmd,
                cwd=tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await repomix_proc.communicate()

            if repomix_proc.returncode != 0:
                raise RepoReadError(f"Erro ao executar repomix:\n{stderr.decode()}")

            logger.debug("Repomix executado com sucesso.")
            return stdout.decode().strip()

    except RepoReadError:
        raise

    except FileNotFoundError as e:
        logger.error("Comando não encontrado (git ou npx ausente no ambiente): %s", e)
        raise RepoReadError("Ambiente sem suporte a git ou npx.") from e

    except asyncio.TimeoutError:
        logger.error("Tempo limite excedido ao processar o repositório '%s'", repo_url)
        raise RepoReadError("Tempo limite excedido durante a leitura do repositório.")

    except Exception as e:
        logger.exception(f"Erro inesperado ao ler o repositório '{repo_url}': {e}")
        raise RepoReadError(f"Erro inesperado: {e}") from e


def send_email_tool(to: str, subject: str, body: str) -> dict:
    """Envia um email usando SMTP.
    
    Requer variáveis de ambiente:
    - SMTP_HOST: servidor SMTP
    - SMTP_PORT: porta (default: 587)
    - SMTP_USER: usuário
    - SMTP_PASSWORD: senha
    - SMTP_FROM: email remetente
    """
    import smtplib
    from email.mime.text import MIMEText
    
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)
    
    if not all([smtp_host, smtp_user, smtp_password]):
        raise ConnectionError("Variáveis SMTP_HOST, SMTP_USER e SMTP_PASSWORD são obrigatórias.")
    
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, [to], msg.as_string())
        
        logger.info(f"Email enviado para '{to}'")
        return {"status": "success", "to": to, "subject": subject}
        
    except Exception as e:
        logger.error(f"Erro ao enviar email para '{to}': {e}")
        raise Exception(f"Erro ao enviar email para '{to}': {e}")
