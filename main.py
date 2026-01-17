# main.py - Bot de Registro para Discord (Railway Otimizado)
import discord
from discord import app_commands
import os
import json
import datetime
import asyncio
import time
from typing import Optional
from keep_alive import keep_alive

# ================= CONFIGURAÇÃO =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

class RegistrationBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.start_time = time.time()
        self.activity_task = None

    async def setup_hook(self):
        # Sincronizar comandos
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} comandos slash sincronizados")
        except Exception as e:
            print(f"⚠️ Erro ao sincronizar comandos: {e}")
        
        # Iniciar task de atividade
        self.activity_task = self.loop.create_task(self.update_activity())

    async def update_activity(self):
        """Atualiza a atividade do bot periodicamente"""
        await self.wait_until_ready()
        
        activities = [
            discord.Activity(type=discord.ActivityType.watching, name="registros"),
            discord.Activity(type=discord.ActivityType.playing, name="/ajuda"),
            discord.Activity(type=discord.ActivityType.listening, name="solicitações")
        ]
        
        while not self.is_closed():
            for activity in activities:
                try:
                    await self.change_presence(activity=activity)
                    await asyncio.sleep(60)  # Muda a cada 60 segundos
                except:
                    await asyncio.sleep(60)

    async def close(self):
        """Limpeza ao fechar o bot"""
        if self.activity_task:
            self.activity_task.cancel()
        await super().close()

bot = RegistrationBot()

# ================= CONFIGURAÇÕES =================
CONFIG_FILE = "config.json"

def load_config():
    """Carrega as configurações do arquivo JSON"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao carregar config: {e}")
            return create_default_config()
    else:
        return create_default_config()

def create_default_config():
    """Cria configuração padrão"""
    default_config = {
        "TOKEN": os.getenv("DISCORD_TOKEN", "SEU_TOKEN_AQUI"),
        "auto_roles": {},
        "tag_config": {},
        "register_channels": {},
        "approval_channels": {},
        "admins": [],
        "super_admins": [],
        "settings": {
            "approval_enabled": True,
            "auto_nickname": True
        }
    }
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print("✅ Arquivo config.json criado")
    except Exception as e:
        print(f"❌ Erro ao criar config: {e}")
    
    return default_config

def save_config(config):
    """Salva as configurações no arquivo JSON"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar config: {e}")
        return False

config = load_config()

# ================= FUNÇÕES AUXILIARES =================
def is_admin(interaction):
    """Verifica se o usuário é admin"""
    user = interaction.user
    
    # Dono do servidor
    if user.id == interaction.guild.owner_id:
        return True
    
    # Super admins configurados
    if user.id in config.get("super_admins", []):
        return True
    
    # Admins configurados
    if user.id in config.get("admins", []):
        return True
    
    # Permissão de administrador no Discord
    if user.guild_permissions.administrator:
        return True
    
    return False

def format_uptime(seconds):
    """Formata o tempo de atividade"""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"

async def update_user_nickname(member, nome, user_id_num, guild_id):
    """Atualiza o nickname do usuário"""
    tag = config["tag_config"].get(guild_id, "")
    
    if tag:
        nickname = f"{tag}・{nome} | {user_id_num}"
    else:
        nickname = f"{nome} | {user_id_num}"
    
    # Limitar a 32 caracteres (limite do Discord)
    if len(nickname) > 32:
        nickname = nickname[:32]
    
    try:
        await member.edit(nick=nickname)
        return True, nickname
    except discord.Forbidden:
        return False, "❌ Sem permissão para alterar nickname"
    except discord.HTTPException as e:
        return False, f"❌ Erro do Discord: {e}"
    except Exception as e:
        return False, f"❌ Erro: {str(e)}"

# ================= COMANDOS SLASH =================

# === CONFIGURAÇÃO ===
@bot.tree.command(name="setup", description="Configurar sistema completo de registro")
@app_commands.describe(
    tag="Tag para novos membros (ex: 77K)",
    cargo="Cargo automático para novos membros",
    canal_registro="Canal onde usuários vão se registrar",
    canal_aprovacao="Canal onde staff aprova registros"
)
async def setup(interaction: discord.Interaction, 
                tag: str, 
                cargo: discord.Role, 
                canal_registro: discord.TextChannel, 
                canal_aprovacao: discord.TextChannel):
    
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores podem usar este comando!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    # Salvar configurações
    config["tag_config"][guild_id] = tag
    config["auto_roles"][guild_id] = cargo.id
    config["register_channels"][guild_id] = canal_registro.id
    config["approval_channels"][guild_id] = canal_aprovacao.id
    
    if save_config(config):
        # Embed de confirmação
        embed = discord.Embed(
            title="✅ **SISTEMA CONFIGURADO**",
            description="Tudo configurado com sucesso!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="🏷️ Tag Configurada", value=f"`{tag}`", inline=True)
        embed.add_field(name="🎭 Cargo Automático", value=cargo.mention, inline=True)
        embed.add_field(name="📝 Canal de Registro", value=canal_registro.mention, inline=True)
        embed.add_field(name="✅ Canal de Aprovação", value=canal_aprovacao.mention, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Criar painéis
        await create_painel_registro(canal_registro, guild_id, tag, cargo)
        await create_painel_aprovacao(canal_aprovacao, guild_id)
    else:
        await interaction.response.send_message("❌ Erro ao salvar configurações!", ephemeral=True)

@bot.tree.command(name="config_tag", description="Configurar ou alterar a tag")
@app_commands.describe(tag="Nova tag (ex: 77K)")
async def config_tag(interaction: discord.Interaction, tag: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    config["tag_config"][guild_id] = tag
    
    if save_config(config):
        await interaction.response.send_message(f"✅ Tag configurada para: `{tag}`", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Erro ao salvar configuração!", ephemeral=True)

@bot.tree.command(name="config_cargo", description="Configurar cargo automático")
@app_commands.describe(cargo="Cargo para aplicar automaticamente")
async def config_cargo(interaction: discord.Interaction, cargo: discord.Role):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    config["auto_roles"][guild_id] = cargo.id
    
    if save_config(config):
        await interaction.response.send_message(f"✅ Cargo automático: {cargo.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Erro ao salvar configuração!", ephemeral=True)

# === ADMINISTRAÇÃO ===
@bot.tree.command(name="add_admin", description="Adicionar administrador ao sistema")
@app_commands.describe(usuario="Usuário para tornar administrador")
async def add_admin(interaction: discord.Interaction, usuario: discord.User):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores do servidor!", ephemeral=True)
        return
    
    if usuario.id not in config["admins"]:
        config["admins"].append(usuario.id)
        if save_config(config):
            await interaction.response.send_message(f"✅ {usuario.mention} adicionado como administrador!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Erro ao salvar configuração!", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ {usuario.mention} já é administrador!", ephemeral=True)

@bot.tree.command(name="add_super_admin", description="Adicionar super administrador (apenas dono)")
@app_commands.describe(usuario="Usuário para tornar super admin")
async def add_super_admin(interaction: discord.Interaction, usuario: discord.User):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Apenas o dono do servidor!", ephemeral=True)
        return
    
    if usuario.id not in config["super_admins"]:
        config["super_admins"].append(usuario.id)
        if save_config(config):
            await interaction.response.send_message(f"👑 {usuario.mention} é agora SUPER ADMIN!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Erro ao salvar configuração!", ephemeral=True)
    else:
        await interaction.response.send_message(f"👑 {usuario.mention} já é super admin!", ephemeral=True)

@bot.tree.command(name="list_admins", description="Listar todos os administradores do sistema")
async def list_admins(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="👥 **LISTA DE ADMINISTRADORES**",
        color=discord.Color.blue()
    )
    
    # Super admins
    super_admins = config.get("super_admins", [])
    if super_admins:
        super_text = ""
        for user_id in super_admins:
            user = interaction.guild.get_member(user_id)
            if user:
                super_text += f"👑 {user.mention} (`{user_id}`)\n"
            else:
                super_text += f"👑 `{user_id}` (usuário não está no servidor)\n"
        embed.add_field(name="SUPER ADMINS", value=super_text or "Nenhum", inline=False)
    
    # Admins normais
    admins = config.get("admins", [])
    if admins:
        admin_text = ""
        for user_id in admins:
            user = interaction.guild.get_member(user_id)
            if user:
                admin_text += f"🛡️ {user.mention} (`{user_id}`)\n"
            else:
                admin_text += f"🛡️ `{user_id}` (usuário não está no servidor)\n"
        embed.add_field(name="ADMINS DO SISTEMA", value=admin_text or "Nenhum", inline=False)
    
    embed.set_footer(text=f"Total: {len(super_admins) + len(admins)} administradores")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# === PAINÉIS ===
@bot.tree.command(name="criar_painel_registro", description="Criar painel de registro no canal atual")
async def criar_painel_registro(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    # Verificar configurações
    tag = config["tag_config"].get(guild_id, "Não configurada")
    cargo_id = config["auto_roles"].get(guild_id)
    cargo = interaction.guild.get_role(cargo_id) if cargo_id else None
    
    await create_painel_registro(interaction.channel, guild_id, tag, cargo)
    
    await interaction.response.send_message("✅ Painel criado!", ephemeral=True)

@bot.tree.command(name="criar_painel_aprovacao", description="Criar painel de aprovação no canal atual")
async def criar_painel_aprovacao(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    await create_painel_aprovacao(interaction.channel, guild_id)
    
    await interaction.response.send_message("✅ Painel criado!", ephemeral=True)

async def create_painel_registro(channel, guild_id, tag, cargo):
    """Cria painel de registro"""
    embed = discord.Embed(
        title="📝 **REGISTRO NO SERVIDOR**",
        description=(
            "**Clique no botão abaixo para solicitar registro!**\n\n"
            "📋 **Informações necessárias:**\n"
            "• Nome completo\n"
            "• Seu ID\n"
            "• Quem te recrutou\n"
            "• Motivo para entrar\n\n"
            f"🏷️ **Seu nickname será:** `{tag}・NOME | ID`\n"
            f"🎭 **Cargo recebido:** {cargo.mention if cargo else 'Não configurado'}"
        ),
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )
    
    embed.set_footer(text="Sistema de registro com aprovação")
    
    button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="📝 Solicitar Registro",
        custom_id=f"registrar_{guild_id}",
        emoji="📝"
    )
    
    view = discord.ui.View(timeout=None)
    view.add_item(button)
    
    await channel.send(embed=embed, view=view)

async def create_painel_aprovacao(channel, guild_id):
    """Cria painel de aprovação"""
    embed = discord.Embed(
        title="✅ **PAINEL DE APROVAÇÃO**",
        description=(
            "**Solicitações de registro aparecerão aqui**\n\n"
            "👨‍⚖️ **Para a staff:**\n"
            "• Use ✅ para aprovar registros\n"
            "• Use ❌ para recusar registros\n\n"
            "⚙️ **Processo automático:**\n"
            "• Tag aplicada automaticamente\n"
            "• Cargo dado automaticamente\n"
            "• Usuário notificado via DM"
        ),
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    
    embed.set_footer(text="Aguardando solicitações...")
    
    await channel.send(embed=embed)

# === SISTEMA DE REGISTRO ===
class RegistroModal(discord.ui.Modal, title="📝 Formulário de Registro"):
    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id
    
    nome = discord.ui.TextInput(
        label="Seu nome completo",
        placeholder="Ex: João Silva",
        max_length=32,
        required=True
    )
    
    user_id = discord.ui.TextInput(
        label="Seu ID",
        placeholder="Ex: 1001, 777, 888",
        max_length=10,
        required=True
    )
    
    recrutador = discord.ui.TextInput(
        label="Quem te recrutou?",
        placeholder="Nome da pessoa que te indicou",
        max_length=32,
        required=True
    )
    
    motivo = discord.ui.TextInput(
        label="Por que quer entrar no servidor?",
        style=discord.TextStyle.paragraph,
        placeholder="Explique seu interesse...",
        max_length=300,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        member = interaction.user
        
        # Verificar canal de aprovação
        app_channel_id = config["approval_channels"].get(self.guild_id)
        if not app_channel_id:
            await interaction.followup.send("❌ Sistema não configurado! Use /setup primeiro.", ephemeral=True)
            return
        
        app_channel = guild.get_channel(app_channel_id)
        if not app_channel:
            await interaction.followup.send("❌ Canal de aprovação não encontrado!", ephemeral=True)
            return
        
        # Embed da solicitação
        embed = discord.Embed(
            title="🔄 **NOVA SOLICITAÇÃO DE REGISTRO**",
            description=f"Usuário: {member.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="👤 Nome", value=self.nome.value, inline=True)
        embed.add_field(name="#️⃣ ID", value=self.user_id.value, inline=True)
        embed.add_field(name="👥 Recrutador", value=self.recrutador.value, inline=True)
        
        # Motivo formatado
        motivo_text = self.motivo.value
        if len(motivo_text) > 150:
            motivo_text = motivo_text[:147] + "..."
        embed.add_field(name="❓ Motivo", value=motivo_text, inline=False)
        
        embed.add_field(name="🆔 Discord ID", value=member.id, inline=True)
        embed.add_field(name="📅 Data", value=datetime.datetime.now().strftime("%d/%m %H:%M"), inline=True)
        
        # Botões de aprovação
        view = AprovacaoView(
            user_id=member.id,
            nome=self.nome.value,
            user_id_num=self.user_id.value,
            recrutador=self.recrutador.value,
            guild_id=self.guild_id
        )
        
        # Enviar para canal de aprovação
        await app_channel.send(embed=embed, view=view)
        
        await interaction.followup.send(
            "✅ **Solicitação enviada com sucesso!**\n"
            f"📋 Sua solicitação foi enviada para {app_channel.mention}\n"
            "⏳ Aguarde a aprovação da staff.",
            ephemeral=True
        )

# === SISTEMA DE APROVAÇÃO ===
class AprovacaoView(discord.ui.View):
    def __init__(self, user_id, nome, user_id_num, recrutador, guild_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nome = nome
        self.user_id_num = user_id_num
        self.recrutador = recrutador
        self.guild_id = guild_id
    
    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.success, custom_id="aprovar_btn")
    async def aprovar_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction):
            await interaction.response.send_message("❌ Apenas staff pode aprovar!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        
        if not member:
            # Atualizar embed se usuário não encontrado
            embed = interaction.message.embeds[0]
            embed.title = "❌ USUÁRIO NÃO ENCONTRADO"
            embed.color = discord.Color.red()
            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send("❌ Usuário saiu do servidor!", ephemeral=True)
            return
        
        # 1. Atualizar nickname
        success_nick, nickname = await update_user_nickname(member, self.nome, self.user_id_num, self.guild_id)
        
        # 2. Aplicar cargo
        cargo_added = False
        cargo_id = config["auto_roles"].get(self.guild_id)
        if cargo_id:
            cargo = guild.get_role(cargo_id)
            if cargo:
                try:
                    await member.add_roles(cargo)
                    cargo_added = True
                except Exception as e:
                    print(f"Erro ao adicionar cargo: {e}")
        
        # 3. Atualizar embed da solicitação
        embed = interaction.message.embeds[0]
        embed.title = "✅ **REGISTRO APROVADO**"
        embed.color = discord.Color.green()
        embed.add_field(name="👤 Aprovado por", value=interaction.user.mention, inline=True)
        
        if success_nick:
            embed.add_field(name="🏷️ Nickname Atualizado", value=nickname, inline=True)
        else:
            embed.add_field(name="⚠️ Nickname", value="Não foi possível alterar", inline=True)
        
        if cargo_added:
            embed.add_field(name="🎭 Cargo", value="✅ Aplicado", inline=True)
        
        embed.add_field(name="⏰ Hora", value=datetime.datetime.now().strftime("%H:%M:%S"), inline=True)
        
        await interaction.message.edit(embed=embed, view=None)
        
        # 4. Notificar usuário
        try:
            notify_embed = discord.Embed(
                title="🎉 **SEU REGISTRO FOI APROVADO!**",
                description=f"Bem-vindo(a) ao **{guild.name}**!",
                color=discord.Color.green()
            )
            
            if success_nick:
                notify_embed.add_field(name="🏷️ Seu Nickname", value=nickname, inline=False)
            
            if cargo_added:
                notify_embed.add_field(name="🎭 Cargo Recebido", value="✅ Recebido com sucesso", inline=False)
            
            notify_embed.add_field(name="👤 Aprovado por", value=interaction.user.name, inline=True)
            notify_embed.set_footer(text="Divirta-se no servidor!")
            
            await member.send(embed=notify_embed)
        except:
            pass  # Usuário tem DM bloqueada
        
        await interaction.followup.send(f"✅ {member.mention} registrado com sucesso!", ephemeral=True)
    
    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id="recusar_btn")
    async def recusar_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction):
            await interaction.response.send_message("❌ Apenas staff pode recusar!", ephemeral=True)
            return
        
        embed = interaction.message.embeds[0]
        embed.title = "❌ **REGISTRO RECUSADO**"
        embed.color = discord.Color.red()
        embed.add_field(name="👤 Recusado por", value=interaction.user.mention, inline=True)
        embed.add_field(name="⏰ Hora", value=datetime.datetime.now().strftime("%H:%M:%S"), inline=True)
        
        await interaction.message.edit(embed=embed, view=None)
        
        # Notificar usuário
        try:
            member = interaction.guild.get_member(self.user_id)
            if member:
                await member.send(f"❌ Seu registro no **{interaction.guild.name}** foi recusado pela staff.")
        except:
            pass
        
        await interaction.response.send_message("❌ Registro recusado!", ephemeral=True)

# === FERRAMENTAS ===
@bot.tree.command(name="limpar", description="Apaga mensagens anteriores do canal")
@app_commands.describe(
    quantidade="Quantidade de mensagens para limpar",
    usuario="Limpar apenas de um usuário específico"
)
async def limpar(interaction: discord.Interaction, 
                quantidade: Optional[int] = 100,
                usuario: Optional[discord.User] = None):
    
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        deleted = 0
        limit = min(quantidade, 100)  # Máximo de 100 por vez
        
        def check(msg):
            if usuario:
                return msg.author.id == usuario.id
            return True
        
        # Tentar bulk delete primeiro
        try:
            deleted_msgs = await interaction.channel.purge(
                limit=limit,
                check=check,
                bulk=True
            )
            deleted = len(deleted_msgs)
        except Exception as e:
            print(f"Erro no bulk delete: {e}")
            await interaction.followup.send(f"❌ Erro: {str(e)[:100]}", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🧹 **LIMPEZA CONCLUÍDA**",
            description=f"Foram deletadas **{deleted}** mensagens",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="📊 Total", value=str(deleted), inline=True)
        embed.add_field(name="📝 Canal", value=interaction.channel.mention, inline=True)
        
        if usuario:
            embed.add_field(name="👤 Filtro", value=usuario.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Erro: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name="status", description="Ver status do sistema")
async def status(interaction: discord.Interaction):
    """Mostra status completo"""
    guild_id = str(interaction.guild.id)
    
    embed = discord.Embed(
        title="📊 **STATUS DO SISTEMA**",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )
    
    # Configurações
    tag = config["tag_config"].get(guild_id, "❌ Não configurada")
    embed.add_field(name="🏷️ Tag", value=f"`{tag}`", inline=True)
    
    cargo_id = config["auto_roles"].get(guild_id)
    if cargo_id:
        cargo = interaction.guild.get_role(cargo_id)
        cargo_text = cargo.mention if cargo else "❌ Não encontrado"
    else:
        cargo_text = "❌ Não configurado"
    embed.add_field(name="🎭 Cargo", value=cargo_text, inline=True)
    
    # Canais
    reg_channel = config["register_channels"].get(guild_id)
    app_channel = config["approval_channels"].get(guild_id)
    
    reg_status = f"<#{reg_channel}>" if reg_channel else "❌ Não configurado"
    app_status = f"<#{app_channel}>" if app_channel else "❌ Não configurado"
    
    embed.add_field(name="📝 Registro", value=reg_status, inline=True)
    embed.add_field(name="✅ Aprovação", value=app_status, inline=True)
    
    # Sistema
    approval = config["settings"].get("approval_enabled", True)
    auto_nickname = config["settings"].get("auto_nickname", True)
    
    embed.add_field(name="🔐 Sistema", value="✅ COM APROVAÇÃO" if approval else "❌ SEM APROVAÇÃO", inline=True)
    embed.add_field(name="🏷️ Nickname Auto", value="✅ Ativado" if auto_nickname else "❌ Desativado", inline=True)
    
    # Bot
    uptime = time.time() - bot.start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    
    embed.add_field(name="🤖 Bot", value="✅ Online", inline=True)
    embed.add_field(name="⏱️ Uptime", value=f"{hours}h {minutes}m", inline=True)
    embed.add_field(name="👥 Membros", value=interaction.guild.member_count, inline=True)
    
    embed.set_footer(text=f"Solicitado por {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ajuda", description="Mostrar todos os comandos disponíveis")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 **CENTRAL DE AJUDA**",
        description="Todos os comandos disponíveis:",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="🔧 **CONFIGURAÇÃO**",
        value=(
            "`/setup` - Configurar tudo de uma vez\n"
            "`/config_tag` - Configurar/alterar tag\n"
            "`/config_cargo` - Configurar cargo automático\n"
            "`/criar_painel_registro` - Criar painel de registro\n"
            "`/criar_painel_aprovacao` - Criar painel de aprovação"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👥 **ADMINISTRAÇÃO**",
        value=(
            "`/add_admin` - Adicionar administrador\n"
            "`/add_super_admin` - Adicionar super admin\n"
            "`/list_admins` - Listar todos os admins"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛠️ **FERRAMENTAS**",
        value=(
            "`/limpar` - Limpar mensagens do canal\n"
            "`/status` - Ver status do sistema\n"
            "`/ajuda` - Mostrar esta mensagem\n"
            "`/ping` - Ver latência do bot\n"
            "`/uptime` - Ver tempo de atividade"
        ),
        inline=False
    )
    
    embed.set_footer(text="Use / antes de cada comando • Bot de Registro")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="Retorna a latência do bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: **{latency}ms**",
        color=discord.Color.green() if latency < 100 else discord.Color.orange() if latency < 300 else discord.Color.red()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="uptime", description="Mostra o tempo de atividade do bot")
async def uptime_command(interaction: discord.Interaction):
    uptime_str = format_uptime(time.time() - bot.start_time)
    
    embed = discord.Embed(
        title="⏰ Tempo de Atividade",
        description=f"**{uptime_str}**",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="📅 Iniciado em", value=datetime.datetime.fromtimestamp(bot.start_time).strftime("%d/%m/%Y %H:%M:%S"))
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# === EVENTOS ===
@bot.event
async def on_ready():
    print("=" * 60)
    print(f"✅ Bot conectado como: {bot.user}")
    print(f"📊 ID: {bot.user.id}")
    print(f"📊 Servidores: {len(bot.guilds)}")
    print(f"📊 Usuários: {sum(g.member_count for g in bot.guilds)}")
    print(f"⏰ Iniciado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    # Atividade inicial
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="solicitações de registro"
    ))

@bot.event
async def on_guild_join(guild):
    print(f"➕ Entrei no servidor: {guild.name} (ID: {guild.id})")
    print(f"👥 Membros: {guild.member_count}")
    print(f"👑 Dono: {guild.owner}")
    print("=" * 60)

@bot.event
async def on_guild_remove(guild):
    print(f"➖ Saí do servidor: {guild.name} (ID: {guild.id})")
    print("=" * 60)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Manipula interações de botões"""
    try:
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get('custom_id', '')
            
            if custom_id.startswith("registrar_"):
                guild_id = custom_id.replace("registrar_", "")
                
                # Verificar se é o canal correto
                reg_channel_id = config["register_channels"].get(guild_id)
                if not reg_channel_id or interaction.channel.id != reg_channel_id:
                    await interaction.response.send_message(
                        "❌ Use o botão no canal de registro correto!",
                        ephemeral=True
                    )
                    return
                
                modal = RegistroModal(guild_id)
                await interaction.response.send_modal(modal)
    except Exception as e:
        print(f"Erro na interação: {e}")

# === INICIALIZAÇÃO ===
def main():
    print("=" * 60)
    print("🤖 BOT DE REGISTRO - RAILWAY OTIMIZADO")
    print("=" * 60)
    print("✅ Sistema de registro com aprovação")
    print("✅ Painéis automáticos")
    print("✅ Comandos slash completos")
    print("✅ Hospedagem Railway pronta")
    print("=" * 60)
    
    # Verificar token
    token = config.get("TOKEN")
    
    if not token or token == "SEU_TOKEN_AQUI":
        print("\n❌ **TOKEN NÃO CONFIGURADO**")
        print("\n📝 **CONFIGURAÇÃO PARA RAILWAY:**")
        print("1. No Railway Dashboard, vá em 'Variables'")
        print("2. Adicione a variável: DISCORD_TOKEN")
        print("3. Cole o token do seu bot")
        print("4. O bot iniciará automaticamente")
        print("\n📍 Obtenha o token em: https://discord.com/developers/applications")
        print("=" * 60)
        return
    
    print("✅ Token configurado")
    print("🚀 Iniciando servidor web e bot...")
    print("=" * 60)
    
    try:
        # Iniciar servidor web para manter online
        keep_alive()
        
        # Iniciar bot
        bot.run(token)
    except discord.LoginFailure:
        print("❌ TOKEN INVÁLIDO!")
        print("Verifique a variável DISCORD_TOKEN no Railway")
    except discord.PrivilegedIntentsRequired:
        print("❌ INTENTS NÃO ATIVADOS!")
        print("1. Acesse: https://discord.com/developers/applications")
        print("2. Selecione seu bot")
        print("3. Vá em 'Bot'")
        print("4. Ative:")
        print("   • PRESENCE INTENT")
        print("   • SERVER MEMBERS INTENT")
        print("   • MESSAGE CONTENT INTENT")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()