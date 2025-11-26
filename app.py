import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime, timedelta
import numpy as np
import os
import socket
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# =============================================================================
# ПОДГРУЖАЕМ СТИЛИ
# =============================================================================
def load_css():
    try:
        with open('assets/style.css', 'r', encoding='utf-8') as f:
            css = f.read()
            st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # Базовый fallback
        st.markdown("""
        <style>
            .main-header { 
                color: #1E88E5; 
                text-align: center; 
                font-size: 2.5rem; 
            }
        </style>
        """, unsafe_allow_html=True)

load_css()

# =============================================================================
# ОСНОВНОЙ КОД
# =============================================================================
st.set_page_config(
    page_title="🍽️ Школа 64 - Анализ питания",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомные стили CSS с улучшенным дизайном
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .section-header {
        font-size: 1.8rem;
        color: #2c3e50;
        border-left: 6px solid #3498db;
        padding-left: 20px;
        margin: 3rem 0 2rem 0;
        font-weight: 600;
        background: linear-gradient(45deg, #2c3e50, #3498db);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .info-box {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 25px;
        border-radius: 20px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(116, 185, 255, 0.3);
    }
    .telegram-box {
        background: linear-gradient(135deg, #0088cc 0%, #005999 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(0, 136, 204, 0.3);
    }
    .stButton button {
        background: linear-gradient(45deg, #FF6B6B, #FF8E53);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 25px;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 5px 15px rgba(255, 107, 107, 0.3);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(255, 107, 107, 0.4);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ПОДКЛЮЧЕНИЕ К SUPABASE
# =============================================================================
@st.cache_resource
def init_supabase():
    try:
        client = create_client(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY")
        )
        return client
    except Exception as e:
        st.error(f"❌ Ошибка подключения к базе данных: {e}")
        return None

@st.cache_data(ttl=300)
def load_real_data(_supabase):
    """Загружает реальные данные из базы"""
    try:
        surveys_response = _supabase.table("surveys").select("*").execute()
        users_response = _supabase.table("users").select("*").execute()
        meal_ratings_response = _supabase.table("meal_ratings").select("*").execute()
        meal_comments_response = _supabase.table("meal_comments").select("*").execute()
        
        surveys_df = pd.DataFrame(surveys_response.data)
        users_df = pd.DataFrame(users_response.data)
        meal_ratings_df = pd.DataFrame(meal_ratings_response.data)
        meal_comments_df = pd.DataFrame(meal_comments_response.data)
        
        return {
            'surveys': surveys_df,
            'users': users_df,
            'meal_ratings': meal_ratings_df,
            'meal_comments': meal_comments_df
        }
    except Exception as e:
        st.error(f"❌ Ошибка загрузки данных: {e}")
        return None

def normalize_class_name(class_name):
    """Нормализует названия классов - оставляем только 10А и 11А"""
    if pd.isna(class_name):
        return None
    
    class_name = str(class_name).strip().upper()
    
    # Все возможные вариации для 10А класса
    if class_name in ['10А', '10A', '10А']:
        return '10А'
    
    # Все возможные вариации для 11А класса
    elif class_name in ['11А', '11A', '11А']:
        return '11А'
    
    # Все остальные классы игнорируем
    else:
        return None

def filter_and_normalize_classes(merged_df):
    """Нормализует классы и оставляет только 10А и 11А"""
    if merged_df.empty or 'class' not in merged_df.columns:
        return merged_df
    
    # Нормализуем названия классов
    merged_df['class_normalized'] = merged_df['class'].apply(normalize_class_name)
    
    # Оставляем только 10А и 11А
    filtered_df = merged_df[merged_df['class_normalized'].notna()].copy()
    filtered_df['class'] = filtered_df['class_normalized']
    
    # Удаляем временную колонку
    filtered_df = filtered_df.drop('class_normalized', axis=1)
    
    return filtered_df

# =============================================================================
# ФУНКЦИИ ДЛЯ ГРАФИКОВ С СИНЕ-ЗЕЛЕНОЙ ПАЛИТРОЙ
# =============================================================================
def create_rating_distribution(data, selected_class=None):
    """Гистограмма распределения оценок"""
    if selected_class and selected_class != "Все классы":
        filtered_data = data[data['class'] == selected_class]
        title = f'📊 Распределение оценок - {selected_class}'
    else:
        filtered_data = data
        title = '📊 Распределение общих оценок'
    
    # Сине-зеленая палитра для гистограммы
    colors = ['#1E88E5', '#2196F3', '#64B5F6', '#4CAF50', '#81C784']
    
    fig = px.histogram(
        filtered_data, 
        x='overall_satisfaction',
        nbins=5,
        title=title,
        color_discrete_sequence=colors,
        labels={'overall_satisfaction': 'Общая оценка', 'count': 'Количество оценок'}
    )
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        bargap=0.1,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def create_class_comparison(data):
    """Сравнение средних оценок по классам"""
    if data.empty:
        return None
        
    class_stats = data.groupby('class')['overall_satisfaction'].agg(['mean', 'count']).reset_index()
    class_stats = class_stats[class_stats['count'] > 0]
    
    # Синяя цветовая шкала
    fig = px.bar(
        class_stats,
        x='class',
        y='mean',
        title='🏫 Сравнение средних оценок по классам',
        color='mean',
        color_continuous_scale=['#64B5F6', '#1E88E5', '#1565C0'],
        labels={'class': 'Класс', 'mean': 'Средняя оценка'}
    )
    fig.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def create_meal_ratings_pie_charts(meal_ratings_df, surveys_df, users_df, selected_class=None, date_range=None):
    """Три круговые диаграммы оценок по типам блюд"""
    
    # Объединяем данные
    merged_ratings = meal_ratings_df.merge(
        surveys_df[['id', 'telegram_id', 'date']], 
        left_on='survey_id', 
        right_on='id'
    ).merge(
        users_df[['telegram_id', 'class']], 
        on='telegram_id'
    )
    
    # Нормализуем и фильтруем классы
    merged_ratings = filter_and_normalize_classes(merged_ratings)
    
    # Применяем фильтры
    if selected_class and selected_class != "Все классы":
        merged_ratings = merged_ratings[merged_ratings['class'] == selected_class]
    
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        merged_ratings = merged_ratings[
            (merged_ratings['date'] >= pd.to_datetime(start_date)) & 
            (merged_ratings['date'] <= pd.to_datetime(end_date))
        ]
    
    if merged_ratings.empty:
        return None
    
    # Сине-зеленая палитра для круговых диаграмм
    color_palette = ['#1E88E5', '#2196F3', '#64B5F6', '#4CAF50', '#81C784']
    
    # Создаем три диаграммы
    meal_types = ['первое', 'второе', 'напиток']
    figs = []
    
    for meal_type in meal_types:
        meal_data = merged_ratings[merged_ratings['meal_type'] == meal_type]
        
        if meal_data.empty:
            fig = go.Figure()
            fig.add_annotation(text=f"Нет данных", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(
                title=f'🍽️ {meal_type.title()}',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
        else:
            rating_counts = meal_data['rating'].value_counts().sort_index()
            
            fig = px.pie(
                values=rating_counts.values,
                names=rating_counts.index.astype(str) + ' ⭐',
                title=f'🍽️ {meal_type.title()}',
                color_discrete_sequence=color_palette
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
        
        figs.append(fig)
    
    return figs

def create_daily_surveys_chart(surveys_df, users_df, selected_class=None, date_range=None):
    """График количества анкет по дням"""
    # Объединяем данные
    merged_data = surveys_df.merge(
        users_df[['telegram_id', 'class']], 
        on='telegram_id',
        how='left'
    )
    
    # Нормализуем и фильтруем классы
    merged_data = filter_and_normalize_classes(merged_data)
    
    if merged_data.empty:
        return None
    
    # Применяем фильтры
    filtered_data = merged_data.copy()
    if selected_class and selected_class != "Все классы":
        filtered_data = filtered_data[filtered_data['class'] == selected_class]
    
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data['date'] >= pd.to_datetime(start_date)) & 
            (filtered_data['date'] <= pd.to_datetime(end_date))
        ]
    
    if filtered_data.empty:
        return None
    
    # Цвета для классов (синий и зеленый)
    class_colors = {'10А': '#1E88E5', '11А': '#4CAF50'}
    
    # Группируем по дате и классу
    if selected_class == "Все классы":
        daily_stats = filtered_data.groupby(['date', 'class']).size().reset_index(name='count')
        
        fig = px.line(
            daily_stats,
            x='date',
            y='count',
            color='class',
            title='📈 Активность голосований по дням',
            color_discrete_map=class_colors,
            labels={'date': 'Дата', 'count': 'Количество анкет', 'class': 'Класс'},
            markers=True
        )
    else:
        daily_stats = filtered_data.groupby('date').size().reset_index(name='count')
        
        # Используем синий цвет для одиночного класса
        fig = px.line(
            daily_stats,
            x='date',
            y='count',
            title=f'📈 Активность голосований - {selected_class}',
            color_discrete_sequence=['#1E88E5'],
            labels={'date': 'Дата', 'count': 'Количество анкет'},
            markers=True
        )
        fig.update_traces(line=dict(width=4))
    
    fig.update_layout(
        xaxis=dict(tickformat='%d.%m.%Y'),
        showlegend=(selected_class == "Все классы"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

# =============================================================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# =============================================================================
def main():
    # ЗАГОЛОВОК С ОПИСАНИЕМ
    st.markdown('<h1 class="main-header">🏫 Школа 64</h1>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Анализ качества питания в школьной столовой</div>', unsafe_allow_html=True)
    
    # ИНФОРМАЦИОННЫЙ БЛОК
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            <div class="info-box">
                <h3>📊 О дашборде</h3>
                <p>Этот дашборд анализирует отзывы учащихся о питании в школьной столовой. 
                Данные собираются через Telegram-бота, где ученики ежедневно оценивают качество блюд.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="telegram-box">
                <h4>🤖 Telegram-бот</h4>
                <p>Присоединяйтесь к оценке питания!</p>
                <a href="https://t.me/foodschool64_bot" target="_blank" style="color: white; text-decoration: none;">
                    <b>@foodschool64_bot</b>
                </a>
            </div>
            """, unsafe_allow_html=True)
    
    # Инициализация Supabase
    supabase = init_supabase()
    if not supabase:
        st.error("❌ Не удалось подключиться к базе данных. Проверьте файл .env")
        return
    
    # Загрузка данных
    with st.spinner('🔄 Загрузка данных...'):
        data_dict = load_real_data(supabase)
    
    if not data_dict:
        return
    
    # Обработка данных
    surveys_df = data_dict['surveys']
    users_df = data_dict['users']
    
    merged_df = surveys_df.merge(users_df, on='telegram_id', how='left')
    merged_df = filter_and_normalize_classes(merged_df)
    
    if not merged_df.empty:
        merged_df['date'] = pd.to_datetime(merged_df['date'])
        surveys_df['date'] = pd.to_datetime(surveys_df['date'])
    
    # =========================================================================
    # БОКОВАЯ ПАНЕЛЬ - ФИЛЬТРЫ
    # =========================================================================
    with st.sidebar:
        st.markdown("### 🎛️ Панель управления")
        st.markdown("---")
        
        # Выбор класса
        available_classes = ["Все классы"]
        if not merged_df.empty and 'class' in merged_df.columns:
            class_counts = merged_df['class'].value_counts()
            for cls, count in class_counts.items():
                available_classes.append(f"{cls} ({count})")
        
        selected_class = st.selectbox("**Выберите класс:**", available_classes)
        
        if selected_class != "Все классы":
            selected_class = selected_class.split(' (')[0]
        
        # Выбор даты
        available_dates = []
        if not merged_df.empty and 'date' in merged_df.columns:
            available_dates = sorted(merged_df['date'].dt.date.unique())
        
        if available_dates:
            min_date = min(available_dates)
            max_date = max(available_dates)
            
            date_range = st.date_input(
                "**Период анализа:**",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if date_range and len(date_range) == 1:
                date_range = (date_range[0], max_date)
        else:
            date_range = None
        
        # Применяем фильтры
        filtered_df = merged_df.copy()
        if selected_class and selected_class != "Все классы":
            filtered_df = filtered_df[filtered_df['class'] == selected_class]
        
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['date'] >= pd.to_datetime(start_date)) & 
                (filtered_df['date'] <= pd.to_datetime(end_date))
            ]
        
        # Статистика
        st.markdown("---")
        st.markdown("### 📈 Статистика")
        st.metric("Всего анкет", len(filtered_df))
        if not filtered_df.empty and 'overall_satisfaction' in filtered_df.columns:
            avg_rating = filtered_df['overall_satisfaction'].mean()
            st.metric("Средняя оценка", f"{avg_rating:.1f}")
    
    # =========================================================================
    # ОСНОВНЫЕ МЕТРИКИ
    # =========================================================================
    st.markdown('<div class="section-header">📊 Общая статистика</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_surveys = len(filtered_df)
        st.metric("📝 Всего оценок", total_surveys)
    
    with col2:
        if not filtered_df.empty and 'overall_satisfaction' in filtered_df.columns:
            avg_rating = filtered_df['overall_satisfaction'].mean()
            st.metric("⭐ Средняя оценка", f"{avg_rating:.1f}")
        else:
            st.metric("⭐ Средняя оценка", "0.0")
    
    with col3:
        if not filtered_df.empty and 'overall_satisfaction' in filtered_df.columns:
            max_rating = filtered_df['overall_satisfaction'].max()
            st.metric("🎯 Максимальная оценка", int(max_rating))
        else:
            st.metric("🎯 Максимальная оценка", "0")
    
    with col4:
        if not filtered_df.empty and 'class' in filtered_df.columns:
            unique_classes = filtered_df['class'].nunique()
            st.metric("🏫 Активных классов", unique_classes)
        else:
            st.metric("🏫 Активных классов", "0")
    
    # =========================================================================
    # ГРАФИКИ
    # =========================================================================
    if not filtered_df.empty:
        # Первая строка графиков
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = create_rating_distribution(filtered_df, selected_class)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = create_class_comparison(filtered_df)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
        
        # Вторая строка графиков
        st.markdown('<div class="section-header">🍽️ Оценки по типам блюд</div>', unsafe_allow_html=True)
        
        pie_charts = create_meal_ratings_pie_charts(
            data_dict['meal_ratings'], 
            data_dict['surveys'], 
            data_dict['users'],
            selected_class,
            date_range
        )
        
        if pie_charts:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(pie_charts[0], use_container_width=True)
            with col2:
                st.plotly_chart(pie_charts[1], use_container_width=True)
            with col3:
                st.plotly_chart(pie_charts[2], use_container_width=True)
        
        # Третий график
        st.markdown('<div class="section-header">📈 Динамика голосований</div>', unsafe_allow_html=True)
        
        fig_daily = create_daily_surveys_chart(
            data_dict['surveys'], 
            data_dict['users'],
            selected_class,
            date_range
        )
        if fig_daily:
            st.plotly_chart(fig_daily, use_container_width=True)
    
    else:
        st.warning("📭 Нет данных для отображения с выбранными фильтрами")
    
    # =========================================================================
    # ФУТЕР
    # =========================================================================
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; color: #7f8c8d; font-size: 0.9rem;">
            <p>📊 Дашборд анализа школьного питания • Школа 64</p>
            <p>🤖 Данные собираются через <a href="https://t.me/foodschool64_bot" target="_blank">Telegram-бота</a></p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()